"""
SMT Verification Module (Optional Z3 Integration)
Formal verification of AWP constraint systems using Z3 solver
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
import sys
import os

# Optional Z3 dependency
try:
    import z3
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False
    z3 = None

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from .constraint_builder import ConstraintSystem, Variable
from .uniqueness_verifier import VerificationResult


@dataclass
class SMTVerificationResult:
    """Result of SMT-based verification"""
    z3_available: bool
    is_satisfiable: bool
    is_unique: bool
    solution: Optional[Dict[str, int]]
    verification_time: float
    smt_formula: str
    error_message: Optional[str] = None


class SMTVerifier:
    """Formal verification using Z3 SMT solver"""
    
    def __init__(self, timeout_ms: int = 10000):
        self.timeout_ms = timeout_ms
        self.z3_available = Z3_AVAILABLE
        
        if not self.z3_available:
            print("Warning: Z3 not available. Install with: pip install z3-solver")
    
    def verify_constraint_system(self, system: ConstraintSystem) -> SMTVerificationResult:
        """
        Verify constraint system using Z3 SMT solver
        
        Args:
            system: Constraint system to verify
            
        Returns:
            SMT verification result
        """
        
        if not self.z3_available:
            return SMTVerificationResult(
                z3_available=False,
                is_satisfiable=False,
                is_unique=False,
                solution=None,
                verification_time=0.0,
                smt_formula="Z3 not available",
                error_message="Z3 solver not installed"
            )
        
        try:
            import time
            start_time = time.time()
            
            # Create Z3 solver context
            solver = z3.Solver()
            solver.set("timeout", self.timeout_ms)
            
            # Create Z3 variables
            z3_vars = {}
            for var in system.variables:
                # Use integer variables for counts
                z3_vars[var.name] = z3.Int(var.name)
                
                # Add non-negativity constraints
                solver.add(z3_vars[var.name] >= 0)
                
                # Add upper bound constraints (reasonable limits)
                solver.add(z3_vars[var.name] <= 1000)  # Reasonable upper bound
            
            # Add known value constraints
            for var_name, value in system.known_values.items():
                if var_name in z3_vars:
                    solver.add(z3_vars[var_name] == int(value))
            
            # Add system constraints (Ax = b)
            for i in range(system.matrix.shape[0]):
                constraint_expr = 0
                for j, var in enumerate(system.variables):
                    coeff = float(system.matrix[i, j])
                    if abs(coeff) > 1e-10:  # Skip near-zero coefficients
                        constraint_expr = constraint_expr + int(coeff * 1000) * z3_vars[var.name]
                
                # Scale RHS by same factor to maintain precision
                rhs_scaled = int(system.rhs[i] * 1000) if i < len(system.rhs) else 0
                solver.add(constraint_expr == rhs_scaled)
            
            # Check satisfiability
            result = solver.check()
            verification_time = time.time() - start_time
            
            if result == z3.sat:
                # Extract solution
                model = solver.model()
                solution = {}
                for var_name, z3_var in z3_vars.items():
                    if model[z3_var] is not None:
                        solution[var_name] = model[z3_var].as_long()
                
                # Check uniqueness by adding negation of current solution
                is_unique = self._check_uniqueness(solver, z3_vars, system.masked_variables, model)
                
                # Generate SMT formula string
                smt_formula = self._generate_smt_formula(solver, z3_vars)
                
                return SMTVerificationResult(
                    z3_available=True,
                    is_satisfiable=True,
                    is_unique=is_unique,
                    solution=solution,
                    verification_time=verification_time,
                    smt_formula=smt_formula
                )
                
            elif result == z3.unsat:
                return SMTVerificationResult(
                    z3_available=True,
                    is_satisfiable=False,
                    is_unique=False,
                    solution=None,
                    verification_time=verification_time,
                    smt_formula=self._generate_smt_formula(solver, z3_vars),
                    error_message="System is unsatisfiable"
                )
                
            else:  # timeout or unknown
                return SMTVerificationResult(
                    z3_available=True,
                    is_satisfiable=False,
                    is_unique=False,
                    solution=None,
                    verification_time=verification_time,
                    smt_formula=self._generate_smt_formula(solver, z3_vars),
                    error_message="Solver timeout or unknown result"
                )
        
        except Exception as e:
            return SMTVerificationResult(
                z3_available=True,
                is_satisfiable=False,
                is_unique=False,
                solution=None,
                verification_time=0.0,
                smt_formula="",
                error_message=f"SMT verification failed: {str(e)}"
            )
    
    def _check_uniqueness(self, solver: 'z3.Solver', z3_vars: Dict[str, 'z3.ArithRef'], 
                         masked_variables: List[str], current_model: 'z3.ModelRef') -> bool:
        """Check if the solution is unique for masked variables"""
        
        if not masked_variables:
            return True
        
        # Push solver state
        solver.push()
        
        try:
            # Add constraint that at least one masked variable has different value
            alternative_constraints = []
            for var_name in masked_variables:
                if var_name in z3_vars and current_model[z3_vars[var_name]] is not None:
                    current_value = current_model[z3_vars[var_name]].as_long()
                    alternative_constraints.append(z3_vars[var_name] != current_value)
            
            if alternative_constraints:
                # At least one masked variable must be different
                solver.add(z3.Or(alternative_constraints))
                
                # Check if alternative solution exists
                result = solver.check()
                is_unique = (result == z3.unsat)  # Unique if no alternative exists
            else:
                is_unique = True  # No masked variables to check
            
            return is_unique
            
        finally:
            # Pop solver state to restore original constraints
            solver.pop()
    
    def _generate_smt_formula(self, solver: 'z3.Solver', z3_vars: Dict[str, 'z3.ArithRef']) -> str:
        """Generate SMT-LIB format formula string"""
        
        try:
            # Get solver assertions
            assertions = solver.assertions()
            
            # Convert to string (simplified)
            formula_parts = []
            
            # Variable declarations
            for var_name in z3_vars:
                formula_parts.append(f"(declare-const {var_name} Int)")
            
            # Assertions
            for assertion in assertions:
                formula_parts.append(f"(assert {assertion})")
            
            formula_parts.append("(check-sat)")
            formula_parts.append("(get-model)")
            
            return "\n".join(formula_parts)
            
        except Exception:
            return "SMT formula generation failed"
    
    def verify_scenario_smt(self, scenario, masked_info: Dict[str, Any] = None) -> SMTVerificationResult:
        """Convenience method to verify scenario using SMT"""
        
        from .constraint_builder import ConstraintSystemBuilder
        
        builder = ConstraintSystemBuilder()
        system = builder.build_from_scenario(scenario, masked_info)
        
        return self.verify_constraint_system(system)
    
    def compare_with_linear_algebra(self, system: ConstraintSystem) -> Dict[str, Any]:
        """Compare SMT results with linear algebra verification"""
        
        from .uniqueness_verifier import UniquenessVerifier
        
        # Linear algebra verification
        la_verifier = UniquenessVerifier()
        la_result = la_verifier.verify_uniqueness(system)
        
        # SMT verification  
        smt_result = self.verify_constraint_system(system)
        
        comparison = {
            'linear_algebra': {
                'is_unique': la_result.is_unique,
                'is_solvable': la_result.solvable,
                'rank_deficiency': la_result.rank_deficiency
            },
            'smt': {
                'z3_available': smt_result.z3_available,
                'is_unique': smt_result.is_unique,
                'is_satisfiable': smt_result.is_satisfiable,
                'verification_time': smt_result.verification_time
            },
            'agreement': {
                'uniqueness': la_result.is_unique == smt_result.is_unique,
                'solvability': la_result.solvable == smt_result.is_satisfiable
            } if smt_result.z3_available else None
        }
        
        return comparison
    
    def export_smt_lib(self, system: ConstraintSystem, filename: str):
        """Export constraint system as SMT-LIB format file"""
        
        if not self.z3_available:
            raise RuntimeError("Z3 not available for SMT-LIB export")
        
        # Build SMT formula
        result = self.verify_constraint_system(system)
        
        # Write to file
        with open(filename, 'w') as f:
            f.write(result.smt_formula)
        
        print(f"SMT-LIB formula exported to: {filename}")
    
    def is_available(self) -> bool:
        """Check if Z3 SMT solver is available"""
        return self.z3_available
    
    def get_version_info(self) -> Dict[str, str]:
        """Get Z3 version information"""
        
        if not self.z3_available:
            return {'z3_available': 'False', 'error': 'Z3 not installed'}
        
        try:
            return {
                'z3_available': 'True',
                'z3_version': z3.get_version_string(),
                'timeout_ms': str(self.timeout_ms)
            }
        except Exception as e:
            return {
                'z3_available': 'True',
                'error': f'Failed to get version: {str(e)}'
            }