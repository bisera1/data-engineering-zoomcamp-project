SELECT
    company,
    COUNT(*) AS job_count
FROM jobs.jobs_table
GROUP BY company
ORDER BY job_count DESC
LIMIT 5;