SELECT
    level,
    MIN(salary_max) AS salary_max,
    AVG(average_salary) AS average_salary
FROM jobs.jobs_table
GROUP BY level
ORDER BY
    CASE
        WHEN level = 'intern' THEN 1
        WHEN level = 'junior' THEN 2
        WHEN level = 'senior' THEN 3
        WHEN level = 'director' THEN 4
        WHEN level = 'manager' THEN 5
        WHEN level = 'lead' THEN 6
        ELSE 4
    END;