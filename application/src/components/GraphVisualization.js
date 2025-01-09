import React, { useEffect, useState } from 'react';
import Graph from 'react-graph-vis';

function GraphVisualization() {
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('http://localhost:3001/api/graph-data')
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        const uniqueNodeIds = new Set(data.nodes.map(node => node.id));
        if (uniqueNodeIds.size !== data.nodes.length) {
          console.error('Duplicate node IDs detected in data');
          const duplicates = data.nodes.filter((node, index, self) =>
            self.findIndex(n => n.id === node.id) !== index
          );
          console.error('Duplicate nodes:', duplicates);
        }
        
        setGraph(data);
      })
      .catch(err => {
        console.error('Error fetching graph data:', err);
        setError(err.message);
      });
  }, []);

  const options = {
    layout: {
      hierarchical: false
    },
    edges: {
      color: "#000000",
      arrows: {
        to: { enabled: true }
      }
    },
    nodes: {
      shape: 'dot',
      size: 10,
      font: {
        size: 12
      }
    },
    physics: {
      enabled: true,
      stabilization: {
        iterations: 100
      }
    },
    height: "600px"
  };

  if (error) {
    return <div>Error loading graph: {error}</div>;
  }

  return (
    <div style={{ height: '600px', border: '1px solid #ddd' }}>
      {graph.nodes.length > 0 ? (
        <Graph
          graph={graph}
          options={options}
        />
      ) : (
        <div>Loading graph data...</div>
      )}
    </div>
  );
}

export default GraphVisualization;