# Graph Types

Complete reference for all 7 graph topologies used in scenario generation.

## Table of Contents

- [Overview](#overview)
- [Graph Types](#graph-types)
  - [Tree](#tree)
  - [Ring](#ring)
  - [Star](#star)
  - [Flow Network](#flow-network)
  - [DAG (Directed Acyclic Graph)](#dag-directed-acyclic-graph)
  - [Complete](#complete)
  - [Bipartite](#bipartite)
- [Graph Metrics](#graph-metrics)
- [Configuration](#configuration)
- [Selection Strategy](#selection-strategy)

---

## Overview

MTP2 uses graph theory to model object transfer networks. Each scenario's transfer pattern follows one of seven graph topologies, creating diverse reasoning challenges.

### Why Graphs?

- **Structured transfers**: Clear sender-receiver relationships
- **Varied complexity**: Different topologies → different reasoning patterns
- **Measurable**: Graph metrics quantify scenario difficulty
- **Realistic**: Models real-world exchange patterns

**Location**: [awp/graphing.py](../awp/graphing.py)

### Graph Components

- **Nodes**: Agents participating in transfers
- **Edges**: Directed edges representing transfers
- **Edge Properties**: Object type, quantity, step number

---

## Graph Types

### Tree

**Type**: Hierarchical directed tree

**Structure**: Parent-child relationships with single root node

**Builder**: `TreeGraphBuilder`

#### Characteristics

- **Directed**: Parent → Children only
- **Acyclic**: No cycles (no circular transfers)
- **Hierarchical**: Clear levels of distribution
- **Connected**: All nodes reachable from root

#### Visual Representation

```
        Root
       /  |  \
      A   B   C
     / \      |
    D   E     F
```

**Example transfers**:
- Root → A, Root → B, Root → C
- A → D, A → E
- C → F

#### Parameters

```yaml
graph:
  parameters:
    branching_factor: 3  # Max children per node
```

#### Metrics

| Metric | Typical Value |
|--------|---------------|
| Density | Low (0.2-0.4) |
| Diameter | Medium (2-4) |
| Avg Branching | 1.0-3.0 |
| Cycle Count | 0 (acyclic) |

#### Use Cases

- Distribution scenarios (one source to many recipients)
- Hierarchical organization transfers
- Supply chain models

#### Example Scenario

```
Scenario: School supplies distribution

Root (Teacher) has 50 pencils
Teacher gives:
  - 15 pencils to Alex
  - 20 pencils to Sam
  - 15 pencils to Riley

Alex redistributes:
  - 7 pencils to Jordan
  - 8 pencils to Casey
```

#### Code Reference

[awp/graphing.py:32](../awp/graphing.py#L32)

---

### Ring

**Type**: Circular directed ring

**Structure**: Agents arranged in a circle, each passing to the next

**Builder**: `RingGraphBuilder`

#### Characteristics

- **Directed**: Clockwise or counterclockwise
- **Cyclic**: Forms a complete cycle
- **Uniform**: Each node has same in-degree and out-degree
- **Connected**: Single circular path

#### Visual Representation

```
     A → B
     ↑   ↓
     D ← C
```

**Transfer sequence**: A → B → C → D → A (cycle)

#### Parameters

No special parameters (uses agent count)

#### Metrics

| Metric | Typical Value |
|--------|---------------|
| Density | Low (0.1-0.3) |
| Diameter | Medium (n/2) |
| Avg Branching | 1.0 (uniform) |
| Cycle Count | 1 (single cycle) |

#### Use Cases

- Circular trading scenarios
- Round-robin exchanges
- Relay race patterns

#### Example Scenario

```
Scenario: Book exchange circle

Alex has 5 books → gives 2 to Sam
Sam has 8 books → gives 3 to Riley
Riley has 4 books → gives 1 to Jordan
Jordan has 6 books → gives 2 to Alex (cycle completes)
```

#### Code Reference

[awp/graphing.py:77](../awp/graphing.py#L77)

---

### Star

**Type**: Hub-and-spoke

**Structure**: Central hub connected to all other nodes

**Builder**: `StarGraphBuilder`

#### Characteristics

- **Directed**: Hub → Spokes (distribution) OR Spokes → Hub (collection)
- **Centralized**: One central node handles all transfers
- **Acyclic**: No cycles
- **High centrality**: Hub has high degree

#### Visual Representation

```
   B   C   D
    \ | /
     Hub
    / | \
   E   F   G
```

**Distribution pattern**: Hub → all others
**Collection pattern**: All others → Hub

#### Variants

1. **Distribution Star**: Hub sends to all spokes
2. **Collection Star**: All spokes send to hub
3. **Mixed Star**: Bidirectional (both distribution and collection)

#### Parameters

No special parameters (automatically selects hub)

#### Metrics

| Metric | Typical Value |
|--------|---------------|
| Density | Medium (0.3-0.5) |
| Diameter | 2 (all nodes 2 hops from hub) |
| Avg Branching | High for hub, 0 for spokes |
| Cycle Count | 0 (acyclic) |

#### Use Cases

- Central distribution points (bank, store, warehouse)
- Collection scenarios (donations, taxes)
- Hub-based logistics

#### Example Scenario

```
Scenario: Food bank distribution

Hub (Food Bank) has 100 items
Distributes to families:
  - 20 items to Alex's family
  - 25 items to Sam's family
  - 15 items to Riley's family
  - 30 items to Jordan's family
  - 10 items to Casey's family
```

#### Code Reference

[awp/graphing.py:102](../awp/graphing.py#L102)

---

### Flow Network

**Type**: Random directed network

**Structure**: Random directed edges between agents

**Builder**: `FlowNetworkBuilder`

#### Characteristics

- **Directed**: Random directional edges
- **Variable connectivity**: Some nodes have more connections than others
- **Possibly cyclic**: May contain cycles
- **Flexible**: Most general topology

#### Visual Representation

```
   A → B → C
   ↓   ↑   ↓
   D → E   F
       ↓   ↑
       G → H
```

**Random connections** based on edge count parameters

#### Parameters

```yaml
graph:
  parameters:
    min_edges: 3
    max_edges: 15
```

#### Metrics

| Metric | Typical Value |
|--------|---------------|
| Density | Variable (0.2-0.8) |
| Diameter | Variable (2-6) |
| Avg Branching | Variable (1.0-4.0) |
| Cycle Count | Variable (0-5) |

#### Use Cases

- Complex trading networks
- Social exchange scenarios
- Unpredictable transfer patterns

#### Example Scenario

```
Scenario: Trading card exchanges

Alex trades with Sam, Riley, Jordan
Sam trades with Riley, Casey
Riley trades with Jordan, Morgan
Jordan trades with Casey
(Random network of bilateral exchanges)
```

#### Code Reference

[awp/graphing.py:139](../awp/graphing.py#L139)

---

### DAG (Directed Acyclic Graph)

**Type**: Directed acyclic graph

**Structure**: Directed edges with no cycles, layers of nodes

**Builder**: `DAGBuilder`

#### Characteristics

- **Directed**: Clear flow direction
- **Acyclic**: No cycles (guaranteed)
- **Layered**: Often forms natural layers
- **Partial order**: Some nodes independent

#### Visual Representation

```
Layer 1:    A   B
           / \ / \
Layer 2:  C   D   E
           \ / \ /
Layer 3:    F   G
```

**Topological ordering**: A, B, C, D, E, F, G (one valid ordering)

#### Parameters

```yaml
graph:
  parameters:
    max_chain_length: 5  # Max path length
```

#### Algorithm

1. Generate random edges
2. Check for cycles using NetworkX
3. If cycle detected, remove edge and retry
4. Repeat until target edge count reached

#### Metrics

| Metric | Typical Value |
|--------|---------------|
| Density | Medium (0.3-0.6) |
| Diameter | Medium (3-5) |
| Avg Branching | Variable (1.5-3.0) |
| Cycle Count | 0 (guaranteed) |

#### Use Cases

- Workflow scenarios
- Production pipelines
- Dependency chains

#### Example Scenario

```
Scenario: Assembly line

Raw materials (A, B) →
  Processing stations (C, D, E) →
    Final products (F, G)

Each stage passes materials forward, no back-flow.
```

#### Code Reference

[awp/graphing.py:176](../awp/graphing.py#L176)

---

### Complete

**Type**: Complete directed graph

**Structure**: Every agent gives to every other agent

**Builder**: `CompleteGraphBuilder`

#### Characteristics

- **Fully connected**: Edge from every node to every other node
- **Directed**: A → B doesn't imply B → A (but often both exist)
- **Maximum density**: Highest possible edge count
- **Symmetric**: Often bidirectional

#### Visual Representation

```
   A ⇄ B
   ⇅ ⇆ ⇅
   C ⇄ D
```

**All pairs connected**: (A→B, A→C, A→D, B→A, B→C, B→D, ...)

#### Density

For n agents: n × (n - 1) directed edges

**Examples**:
- 3 agents: 6 edges
- 4 agents: 12 edges
- 5 agents: 20 edges

#### Parameters

No special parameters (determined by agent count)

#### Metrics

| Metric | Typical Value |
|--------|---------------|
| Density | 1.0 (maximum) |
| Diameter | 1 (direct connections) |
| Avg Branching | n - 1 |
| Cycle Count | High (many cycles) |

#### Use Cases

- Complex trading scenarios
- Full market exchanges
- Complete redistribution

#### Example Scenario

```
Scenario: Complete gift exchange

Every person gives a gift to every other person:
- Alex gives to Sam, Riley, Jordan
- Sam gives to Alex, Riley, Jordan
- Riley gives to Alex, Sam, Jordan
- Jordan gives to Alex, Sam, Riley

Total: 4 × 3 = 12 transfers
```

#### Warning

- **High complexity**: Many transfers for even small agent counts
- **Long scenarios**: Can produce very lengthy stories
- **Resource intensive**: Use for small agent counts only (3-5)

#### Code Reference

[awp/graphing.py:215](../awp/graphing.py#L215)

---

### Bipartite

**Type**: Two-group bipartite graph

**Structure**: Two distinct groups, transfers only between groups

**Builder**: `BipartiteGraphBuilder`

#### Characteristics

- **Partitioned**: Agents divided into two groups
- **Cross-group only**: No transfers within same group
- **Directed**: Group A → Group B or vice versa
- **Balanced or unbalanced**: Groups can have different sizes

#### Visual Representation

```
Group A:    A1  A2  A3
             |\/|\/|
             |/\|/\|
Group B:    B1  B2
```

**Only cross-group edges**: A1 → B1, A2 → B2, etc.

#### Partitioning

Agents split into two groups:
```python
group_a = agents[:n//2]
group_b = agents[n//2:]
```

#### Parameters

```yaml
graph:
  parameters:
    min_edges: 3
    max_edges: 15
```

#### Metrics

| Metric | Typical Value |
|--------|---------------|
| Density | Medium (0.3-0.6) |
| Diameter | 3-4 |
| Avg Branching | Variable |
| Cycle Count | Even lengths only (2, 4, 6...) |

#### Use Cases

- Buyer-seller scenarios
- Student-teacher exchanges
- Two-party trading

#### Example Scenario

```
Scenario: Farmers market

Farmers (Group A):
- Farmer Alex
- Farmer Sam
- Farmer Riley

Customers (Group B):
- Customer Jordan
- Customer Casey

Transfers (farmers sell to customers only):
- Farmer Alex sells apples to Customer Jordan
- Farmer Sam sells cookies to Customer Casey
- Farmer Riley sells oranges to Customer Jordan
```

#### Code Reference

[awp/graphing.py:246](../awp/graphing.py#L246)

---

## Graph Metrics

Metrics quantify graph complexity and structure.

### Density

**Formula**: `edges / (nodes × (nodes - 1))`

**Range**: 0.0 (no edges) to 1.0 (complete graph)

**Interpretation**:
- < 0.3: Sparse
- 0.3 - 0.6: Medium
- > 0.6: Dense

**Example**:
- 5 nodes, 6 edges: 6 / (5 × 4) = 0.3

### Diameter

**Definition**: Longest shortest path between any two nodes

**Calculation**: Using NetworkX `diameter()` (for connected graphs)

**Interpretation**:
- 1: Direct connections (star, complete)
- 2-3: Small world
- 4+: Large, sparse network

**Example**:
- Chain A → B → C → D: diameter = 3

### Average Branching Factor

**Formula**: `sum(out_degree) / nodes_with_out_edges`

**Interpretation**:
- 1.0: Chain or ring
- 2-3: Tree-like
- > 4: Highly branched

**Example**:
```
Node A → B, C (out-degree: 2)
Node B → D (out-degree: 1)
Node C, D (out-degree: 0)

Avg = (2 + 1) / 2 = 1.5
```

### Cycle Count

**Definition**: Number of simple cycles in the graph

**Calculation**: Using NetworkX `simple_cycles()`

**Interpretation**:
- 0: Acyclic (tree, DAG)
- 1: Single cycle (ring)
- > 1: Complex feedback loops

**Example**:
```
A → B → C → A (1 cycle)
```

### Metrics Summary Table

| Graph Type | Density | Diameter | Avg Branching | Cycles |
|------------|---------|----------|---------------|--------|
| Tree | Low | Medium | Medium | 0 |
| Ring | Low | Medium | 1.0 | 1 |
| Star | Medium | 2 | High/Low | 0 |
| Flow | Variable | Variable | Variable | Variable |
| DAG | Medium | Medium | Variable | 0 |
| Complete | 1.0 | 1 | Max | Many |
| Bipartite | Medium | 3-4 | Variable | Even |

---

## Configuration

### Enabling Graph Types

```yaml
graph:
  types:
    - tree
    - ring
    - star
    - flow
    - dag
    - complete
    - bipartite
```

**Note**: Enable only desired types. Generator randomly selects from enabled types.

### Graph Parameters

```yaml
graph:
  parameters:
    max_chain_length: 5       # For DAG
    branching_factor: 3       # For Tree
    min_edges: 3              # For Flow, Bipartite
    max_edges: 15             # For Flow, Bipartite
```

### Complexity Weights

Graph metrics contribute to scenario complexity:

```yaml
complexity:
  weights:
    diameter: 1.0
    density: 1.5
    branching: 1.0
    cycles: 2.0
```

**Complexity Formula**:
```python
complexity = (
    1.0 × diameter +
    1.5 × density +
    1.0 × avg_branching +
    2.0 × cycle_count +
    ...
)
```

---

## Selection Strategy

### Random Selection

Generator randomly selects from enabled types:

```python
graph_type = random.choice(config.graph.types)
builder = GRAPH_BUILDERS[graph_type](config, rng)
graph = builder.build(agents, num_transfers)
```

### Difficulty Matching

Certain graph types suit certain difficulties:

| Difficulty | Recommended Types |
|------------|-------------------|
| Simple | tree, ring, star |
| Moderate | flow, dag, bipartite |
| Complex | flow, dag, complete |
| Extreme | complete, flow (high edges) |

### Custom Selection

```python
def select_graph_type(difficulty):
    if difficulty == "simple":
        return random.choice(["tree", "ring", "star"])
    elif difficulty == "moderate":
        return random.choice(["flow", "dag", "bipartite"])
    else:
        return random.choice(["flow", "dag", "complete"])
```

---

## Graph Builder API

All builders implement the same interface:

```python
class GraphBuilder:
    def __init__(self, config, rng):
        self.config = config
        self.rng = rng

    def build(self, agents: List[str], num_edges: int) -> nx.DiGraph:
        """Build graph with specified agents and edge count."""
        raise NotImplementedError
```

### Usage

```python
from awp.graphing import TreeGraphBuilder

# Create builder
builder = TreeGraphBuilder(config, rng)

# Build graph
agents = ["Alex", "Sam", "Riley", "Jordan"]
graph = builder.build(agents, num_edges=6)

# Inspect graph
print(f"Nodes: {list(graph.nodes())}")
print(f"Edges: {list(graph.edges())}")
print(f"Density: {nx.density(graph):.2f}")
```

---

## Visualization

While MTP2 doesn't include built-in visualization, you can visualize graphs using NetworkX:

```python
import networkx as nx
import matplotlib.pyplot as plt

# Build graph
graph = builder.build(agents, num_edges=6)

# Visualize
plt.figure(figsize=(10, 8))
pos = nx.spring_layout(graph)
nx.draw(graph, pos, with_labels=True, node_color='lightblue',
        node_size=1500, font_size=12, arrows=True)
plt.title(f"{graph_type.capitalize()} Graph")
plt.show()
```

---

## Best Practices

### 1. Match Graph Type to Scenario

Choose appropriate graph type for your scenario:
- **Distribution**: tree, star
- **Trading**: flow, bipartite
- **Circular**: ring
- **Complex**: complete, flow

### 2. Control Edge Count

More edges = more transfers = longer stories:

```yaml
graph:
  parameters:
    min_edges: 3
    max_edges: 10  # Limit for readability
```

### 3. Balance Graph Types

Use variety of graph types:

```yaml
graph:
  types:
    - tree      # 30%
    - ring      # 15%
    - star      # 15%
    - flow      # 25%
    - dag       # 15%
```

### 4. Consider Agent Count

| Agents | Suitable Types |
|--------|----------------|
| 3-5 | All types |
| 6-10 | Avoid complete |
| 10+ | tree, dag, flow only |

### 5. Validate Graph Properties

```python
# Ensure graph is connected (for meaningful scenarios)
if not nx.is_weakly_connected(graph):
    print("Warning: Disconnected graph")

# Check for isolated nodes
isolated = list(nx.isolates(graph))
if isolated:
    print(f"Warning: Isolated nodes: {isolated}")
```

---

## Advanced Usage

### Custom Graph Builder

Create your own graph topology:

```python
class CustomGraphBuilder(GraphBuilder):
    def build(self, agents, num_edges):
        graph = nx.DiGraph()
        graph.add_nodes_from(agents)

        # Your custom logic
        # ...

        return graph

# Register builder
GRAPH_BUILDERS["custom"] = CustomGraphBuilder
```

### Graph Constraints

Add constraints to graph generation:

```python
def build_with_constraints(self, agents, num_edges):
    graph = self._build_base_graph(agents, num_edges)

    # Constraint: No node with more than 3 out-edges
    for node in graph.nodes():
        if graph.out_degree(node) > 3:
            # Remove excess edges
            excess = list(graph.out_edges(node))[3:]
            graph.remove_edges_from(excess)

    return graph
```

### Hybrid Graphs

Combine multiple topologies:

```python
def build_hybrid(agents):
    # Start with tree
    graph = TreeGraphBuilder().build(agents[:n//2], n//4)

    # Add ring component
    ring = RingGraphBuilder().build(agents[n//2:], n//4)

    # Merge
    graph = nx.compose(graph, ring)

    return graph
```
