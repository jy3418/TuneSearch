DROP MATERIALIZED VIEW IF EXISTS calc_idf;

CREATE MATERIALIZED VIEW calc_idf
AS
  SELECT
    T.song_id,
    T.token AS token,
    T.count AS tf,
    DF AS idf,
    T.count * (LOG(J_Count) - LOG(DF)) AS tfidf
  FROM (
    SELECT
      token,
      COUNT(song_id) AS DF
    FROM token
    GROUP BY token
  ) D
  JOIN token T
  ON T.token = D.token
  CROSS JOIN (
    SELECT
      COUNT(DISTINCT(song_id)) AS J_Count
    FROM song
  ) J
;

DROP TABLE IF EXISTS tfidf CASCADE;

SELECT
  song_id,
  token,
  tfidf AS score
INTO tfidf
FROM calc_idf
;