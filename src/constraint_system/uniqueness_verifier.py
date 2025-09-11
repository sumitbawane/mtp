"""
Uniqueness Verification System for AWP Constraint Systems
Verifies that masked variables have unique solutions
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import scipy.linalg
from .constraint_builder import ConstraintSystem, ConstraintSystemBuilder


@dataclass
class VerificationResult:
    """Result of uniqueness verification"""
    is_unique: bool
    rank_deficiency: int
    condition_number: float
    solvable: bool
    redundant_constraints: List[int]
    message: str


class UniquenessVerifier:
    """Verifies uniqueness of solutions in AWP constraint systems"""
    
    def __init__(self, tolerance: float = 1e-10):
        self.tolerance = tolerance
        
    def verify_uniqueness(self, system: ConstraintSystem) -> VerificationResult:
        """
        Verify that the constraint system has a unique solution for masked variables
        
        Args:
            system: Complete constraint system
            
        Returns:
            VerificationResult with uniqueness information
        """
        if not system.masked_variables:
            return VerificationResult(
                is_unique=True,
                rank_deficiency=0,
                condition_number=1.0,
                solvable=True,
                redundant_constraints=[],
                message="No masked variables - trivially unique"
            )
        
        # Extract subsystem for masked variables only
        builder = ConstraintSystemBuilder()
        A_masked, b_adjusted, masked_vars = builder.extract_masked_system(system)
        
        if A_masked.size == 0:
            return VerificationResult(
                is_unique=True,
                rank_deficiency=0,
                condition_number=1.0,
                solvable=True,
                redundant_constraints=[],
                message="Empty masked system - trivially unique"
            )
        
        return self._analyze_linear_system(A_masked, b_adjusted, masked_vars)
    
    def _analyze_linear_system(self, A: np.ndarray, b: np.ndarray, 
                              var_names: List[str]) -> VerificationResult:
        """Analyze linear system Ax = b for uniqueness"""
        m, n = A.shape  # m constraints, n variables
        
        # Check if system is solvable
        try:
            # Compute ranks
            rank_A = np.linalg.matrix_rank(A, tol=self.tolerance)
            
            if m == 0 or n == 0:
                return VerificationResult(
                    is_unique=n == 0,
                    rank_deficiency=0,
                    condition_number=1.0,
                    solvable=True,
                    redundant_constraints=[],
                    message="Empty system"
                )
            
            # Augmented matrix [A|b] for consistency check
            Ab = np.column_stack([A, b.reshape(-1, 1)])
            rank_Ab = np.linalg.matrix_rank(Ab, tol=self.tolerance)
            
            # System is consistent if rank(A) == rank([A|b])
            solvable = (rank_A == rank_Ab)
            
            if not solvable:
                return VerificationResult(
                    is_unique=False,
                    rank_deficiency=rank_A - min(m, n),
                    condition_number=float('inf'),
                    solvable=False,
                    redundant_constraints=[],
                    message="Inconsistent system - no solution exists"
                )
            
            # For uniqueness: need rank(A) == n (number of variables)
            rank_deficiency = n - rank_A
            is_unique = (rank_deficiency == 0)
            
            # Condition number (if system is square and full rank)
            condition_number = 1.0
            if m == n and rank_A == n:
                try:
                    condition_number = np.linalg.cond(A)
                except np.linalg.LinAlgError:
                    condition_number = float('inf')
            
            # Find redundant constraints
            redundant_constraints = self._find_redundant_constraints(A)
            
            # Generate message
            if is_unique:
                message = f"Unique solution exists. System is well-determined."
            elif rank_deficiency > 0:
                message = f"Under-determined system. {rank_deficiency} degrees of freedom."
            else:
                message = f"Over-determined system. {m - rank_A} redundant constraints."
            
            return VerificationResult(
                is_unique=is_unique,
                rank_deficiency=rank_deficiency,
                condition_number=condition_number,
                solvable=solvable,
                redundant_constraints=redundant_constraints,
                message=message
            )
            
        except Exception as e:
            return VerificationResult(
                is_unique=False,
                rank_deficiency=-1,
                condition_number=float('inf'),
                solvable=False,
                redundant_constraints=[],
                message=f"Error in analysis: {str(e)}"
            )
    
    def _find_redundant_constraints(self, A: np.ndarray) -> List[int]:
        """Find redundant (linearly dependent) constraints"""
        m, n = A.shape
        if m <= n:
            return []  # Can't have redundant constraints if m <= n
        
        try:
            # Use QR decomposition to find linear dependencies
            Q, R, P = scipy.linalg.qr(A.T, pivoting=True, mode='full')
            
            # Find near-zero diagonal elements in R
            diagonal = np.abs(np.diag(R))
            redundant_indices = []
            
            for i in range(len(diagonal)):
                if i < len(diagonal) and diagonal[i] < self.tolerance:
                    # This corresponds to a redundant constraint
                    if P[i] < m:
                        redundant_indices.append(P[i])
            
            return sorted(redundant_indices)
            
        except Exception:
            # Fallback: use SVD
            try:
                U, s, Vt = np.linalg.svd(A, full_matrices=True)
                rank = np.sum(s > self.tolerance)
                
                if rank < m:
                    # Find which constraints are redundant
                    redundant_indices = []
                    for i in range(rank, m):
                        # Find the constraint most aligned with this null space vector
                        null_vec = U[:, i]
                        max_coeff_idx = np.argmax(np.abs(null_vec))
                        redundant_indices.append(max_coeff_idx)
                    
                    return sorted(list(set(redundant_indices)))
                
                return []
                
            except Exception:
                return []
    
    def suggest_fixes(self, result: VerificationResult, system: ConstraintSystem) -> List[str]:
        """Suggest fixes for non-unique systems"""
        suggestions = []
        
        if not result.solvable:
            suggestions.append("System is inconsistent. Check for contradictory constraints.")
            suggestions.append("Verify that transfer quantities and inventories are compatible.")
            
        elif not result.is_unique:
            if result.rank_deficiency > 0:
                suggestions.append(f"System is under-determined ({result.rank_deficiency} degrees of freedom).")
                suggestions.append("Add more constraints or mask fewer variables.")
                suggestions.append("Consider masking different variables to create a well-determined system.")
                
        if result.redundant_constraints:
            suggestions.append(f"Remove redundant constraints: {result.redundant_constraints}")
            
        if result.condition_number > 1e12:
            suggestions.append("System is ill-conditioned. Small changes may cause large solution changes.")
            suggestions.append("Consider using different numerical values or constraint formulation.")
            
        return suggestions
    
    def verify_scenario_uniqueness(self, scenario, masked_info: Dict[str, Any] = None) -> VerificationResult:
        """Convenience method to verify scenario uniqueness directly"""
        builder = ConstraintSystemBuilder()
        system = builder.build_from_scenario(scenario, masked_info)
        return self.verify_uniqueness(system)
    
    def is_well_posed(self, system: ConstraintSystem) -> bool:
        """Check if the constraint system is well-posed (unique and stable)"""
        result = self.verify_uniqueness(system)
        return (result.is_unique and 
                result.solvable and 
                result.condition_number < 1e10)