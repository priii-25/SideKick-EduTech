const express = require('express');
const cors = require('cors'); 
const neo4j = require('neo4j-driver');
const app = express();
app.use(cors());
app.use(express.json());

const driver = neo4j.driver(
  'bolt://localhost:7687', 
  neo4j.auth.basic('neo4j', '-')
);

app.get('/api/graph-data', async (req, res) => {
  const session = driver.session({ database: 'jobsskills' });
  try {
    const result = await session.run(`
      MATCH (n)-[r]->(m)
      RETURN
        id(n) AS sourceId,
        n.name AS sourceName,
        id(m) AS targetId,
        m.name AS targetName,
        type(r) AS relationshipType
    `);

    const nodesMap = {};
    const edges = [];

    result.records.forEach(record => {
      const sourceId = record.get('sourceId').toString();
      const sourceName = record.get('sourceName');
      const targetId = record.get('targetId').toString();
      const targetName = record.get('targetName');
      const relationshipType = record.get('relationshipType');

      if (!nodesMap[sourceId]) {
        nodesMap[sourceId] = { id: sourceId, label: sourceName };
      }
      if (!nodesMap[targetId]) {
        nodesMap[targetId] = { id: targetId, label: targetName };
      }

      edges.push({
        from: sourceId,
        to: targetId,
        label: relationshipType
      });
    });

    const nodes = Object.values(nodesMap);
    res.json({ nodes, edges });
  } catch (error) {
    console.error('Error fetching graph data from Neo4j:', error);
    res.status(500).send('Error fetching graph data from Neo4j');
  } finally {
    await session.close();
  }
});

app.listen(3001, () => {
  console.log('Server is running on port 3001');
});