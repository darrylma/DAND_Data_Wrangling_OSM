.mode csv
.import nodes.csv nodes
.import ways.csv ways
.import nodes_tags.csv nodes_tags
delete from nodes_tags where id = 'id';
.import ways_tags.csv ways_tags
delete from ways_tags where id = 'id';
.import ways_nodes.csv ways_nodes
delete from ways_nodes where id = 'id';
