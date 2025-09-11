"""
Constraint System Builder for AWP Mathematical Verification
Converts AWP scenarios into linear constraint matrices (Ax = b)
"""

import numpy as np
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scenario_core import Transfer, Agent, Scenario


@dataclass
class Variable:
    """Represents a variable in the constraint system"""
    name: str
    var_type: str  # 'initial', 'final', 'transfer'
    agent: str
    object_type: str
    transfer_id: Optional[int] = None
    is_masked: bool = False


@dataclass  
class ConstraintSystem:
    """Complete linear constraint system representation"""
    matrix: np.ndarray  # Coefficient matrix A
    rhs: np.ndarray     # Right-hand side vector b
    variables: List[Variable]  # Variable definitions
    known_values: Dict[str, float]  # Known variable values
    masked_variables: List[str]  # Variables that are masked/unknown
    
    def get_variable_index(self, var_name: str) -> int:
        """Get index of variable in the system"""
        for i, var in enumerate(self.variables):
            if var.name == var_name:
                return i
        return -1


class ConstraintSystemBuilder:
    """Builds linear constraint systems from AWP scenarios"""
    
    def __init__(self):
        self.variable_counter = 0
        
    def build_from_scenario(self, scenario: Scenario, 
                           masked_info: Dict[str, Any] = None) -> ConstraintSystem:
        """
        Build constraint system from scenario
        
        Args:
            scenario: The AWP scenario
            masked_info: Information about what's masked in the problem
            
        Returns:
            ConstraintSystem with matrix representation
        """
        variables = []
        constraints = []
        known_values = {}
        masked_variables = []
        
        # Create variables for initial and final inventories
        for agent in scenario.agents:
            for obj_type in scenario.object_types:
                # Initial inventory variable
                init_var = Variable(
                    name=f"init_{agent.name}_{obj_type}",
                    var_type="initial",
                    agent=agent.name,
                    object_type=obj_type
                )
                variables.append(init_var)
                
                # Final inventory variable  
                final_var = Variable(
                    name=f"final_{agent.name}_{obj_type}",
                    var_type="final",
                    agent=agent.name,
                    object_type=obj_type
                )
                variables.append(final_var)
                
                # Set known values from scenario
                init_count = agent.initial_inventory.get(obj_type, 0)
                final_count = agent.final_inventory.get(obj_type, 0)
                
                known_values[init_var.name] = init_count
                known_values[final_var.name] = final_count
        
        # Create variables for transfers
        for transfer in scenario.transfers:
            transfer_var = Variable(
                name=f"transfer_{transfer.transfer_id}_{transfer.from_agent}_{transfer.to_agent}_{transfer.object_type}",
                var_type="transfer",
                agent=transfer.from_agent,
                object_type=transfer.object_type,
                transfer_id=transfer.transfer_id
            )
            variables.append(transfer_var)
            known_values[transfer_var.name] = transfer.quantity
            
        # Apply masking information
        if masked_info:
            self._apply_masking(variables, known_values, masked_variables, masked_info)
        
        # Build constraint matrix
        matrix, rhs = self._build_constraint_matrix(variables, scenario, known_values)
        
        return ConstraintSystem(
            matrix=matrix,
            rhs=rhs,
            variables=variables,
            known_values=known_values,
            masked_variables=masked_variables
        )
    
    def _apply_masking(self, variables: List[Variable], known_values: Dict[str, float],
                      masked_variables: List[str], masked_info: Dict[str, Any]):
        """Apply masking rules to variables"""
        mask_type = masked_info.get('masking_type', 'none')
        
        if mask_type == 'mask_initial_count':
            # Find target agent/object from masked_info
            target_agent = masked_info.get('target_agent')
            target_object = masked_info.get('target_object')
            
            if target_agent and target_object:
                var_name = f"init_{target_agent}_{target_object}"
                if var_name in known_values:
                    # Move to masked variables
                    masked_variables.append(var_name)
                    del known_values[var_name]
                    
                    # Mark variable as masked
                    for var in variables:
                        if var.name == var_name:
                            var.is_masked = True
                            
        elif mask_type == 'quantity_substitution':
            # Mask specific transfer quantities
            for transfer_id in masked_info.get('masked_transfers', []):
                for var in variables:
                    if var.var_type == 'transfer' and var.transfer_id == transfer_id:
                        if var.name in known_values:
                            masked_variables.append(var.name)
                            del known_values[var.name]
                            var.is_masked = True
    
    def _build_constraint_matrix(self, variables: List[Variable], scenario: Scenario,
                               known_values: Dict[str, float]) -> Tuple[np.ndarray, np.ndarray]:
        """Build the constraint matrix A and RHS vector b"""
        n_vars = len(variables)
        constraints = []
        rhs_values = []
        
        # Conservation constraints: final = initial + received - given
        for agent in scenario.agents:
            for obj_type in scenario.object_types:
                constraint_row = np.zeros(n_vars)
                
                # Get variable indices
                init_idx = self._get_var_index(variables, f"init_{agent.name}_{obj_type}")
                final_idx = self._get_var_index(variables, f"final_{agent.name}_{obj_type}")
                
                if init_idx >= 0 and final_idx >= 0:
                    # final - initial = net_transfers
                    constraint_row[final_idx] = 1
                    constraint_row[init_idx] = -1
                    
                    # Add transfer effects
                    net_transfer = 0
                    for transfer in scenario.transfers:
                        if transfer.object_type == obj_type:
                            if transfer.to_agent == agent.name:
                                # Received transfer (positive)
                                transfer_idx = self._get_transfer_var_index(variables, transfer)
                                if transfer_idx >= 0:
                                    constraint_row[transfer_idx] = 1
                                else:
                                    net_transfer += transfer.quantity
                                    
                            elif transfer.from_agent == agent.name:
                                # Given transfer (negative)
                                transfer_idx = self._get_transfer_var_index(variables, transfer)
                                if transfer_idx >= 0:
                                    constraint_row[transfer_idx] = -1
                                else:
                                    net_transfer -= transfer.quantity
                    
                    constraints.append(constraint_row)
                    rhs_values.append(net_transfer)
        
        # Non-negativity constraints (implicit - handled by bounds in solver)
        
        matrix = np.array(constraints) if constraints else np.zeros((0, n_vars))
        rhs = np.array(rhs_values) if rhs_values else np.zeros(0)
        
        return matrix, rhs
    
    def _get_var_index(self, variables: List[Variable], var_name: str) -> int:
        """Get index of variable by name"""
        for i, var in enumerate(variables):
            if var.name == var_name:
                return i
        return -1
    
    def _get_transfer_var_index(self, variables: List[Variable], transfer: Transfer) -> int:
        """Get index of transfer variable"""
        var_name = f"transfer_{transfer.transfer_id}_{transfer.from_agent}_{transfer.to_agent}_{transfer.object_type}"
        return self._get_var_index(variables, var_name)
    
    def extract_masked_system(self, system: ConstraintSystem) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Extract subsystem for masked variables only
        
        Returns:
            A_masked: Constraint matrix for masked variables
            b_adjusted: RHS adjusted for known variables
            masked_var_names: Names of masked variables
        """
        if not system.masked_variables:
            return np.zeros((0, 0)), np.zeros(0), []
            
        # Get indices of masked variables
        masked_indices = []
        for var_name in system.masked_variables:
            idx = system.get_variable_index(var_name)
            if idx >= 0:
                masked_indices.append(idx)
        
        if not masked_indices:
            return np.zeros((0, 0)), np.zeros(0), []
            
        # Extract submatrix for masked variables
        A_masked = system.matrix[:, masked_indices]
        
        # Adjust RHS by subtracting known variable contributions
        b_adjusted = system.rhs.copy()
        known_indices = [i for i in range(len(system.variables)) 
                        if system.variables[i].name not in system.masked_variables]
        
        if known_indices:
            A_known = system.matrix[:, known_indices]
            known_values_vec = np.array([system.known_values.get(system.variables[i].name, 0) 
                                       for i in known_indices])
            b_adjusted = b_adjusted - A_known @ known_values_vec
        
        return A_masked, b_adjusted, system.masked_variables