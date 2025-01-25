import React, { useEffect, useState } from 'react';
import Graph from 'react-graph-vis';

function GraphVisualization() {
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('http://localhost:5000/api/graph-data')
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        const uniqueNodes = Array.from(
          new Map(data.nodes.map(node => [node.id, node])).values()
        );
  
        const uniqueEdges = Array.from(
          new Map(
            data.edges.map(edge => [`${edge.from}-${edge.to}`, edge])
          ).values()
        );
  
        if (uniqueNodes.length !== data.nodes.length) {
          console.warn(
            `Duplicate node IDs were removed: ${data.nodes.length - uniqueNodes.length}`
          );
        }
  
        if (uniqueEdges.length !== data.edges.length) {
          console.warn(
            `Duplicate edges were removed: ${data.edges.length - uniqueEdges.length}`
          );
        }
  
        setGraph({
          nodes: uniqueNodes,
          edges: uniqueEdges,
        });
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