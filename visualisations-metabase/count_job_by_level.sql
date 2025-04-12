SELECT
    level,
    COUNT(*) AS job_count
FROM jobs.jobs_table
WHERE level IN ('intern', 'junior', 'senior', 'director', 'manager', 'lead')
GROUP BY level
ORDER BY
    CASE
        WHEN level = 'intern' THEN 1
        WHEN level = 'junior' THEN 2
        WHEN level = 'senior' THEN 3
        WHEN level = 'director' THEN 4
        WHEN level = 'manager' THEN 5
        WHEN level = 'lead' THEN 6
    END;
