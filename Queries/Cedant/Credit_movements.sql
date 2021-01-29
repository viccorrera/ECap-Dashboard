SELECT
    CASE
        WHEN t.COMP_ID_PREV IS NULL THEN t.COMP_ID_CURR
        ELSE t.COMP_ID_PREV
    END AS COMP_ID,
    ECAP_PREV_QRT,
    ECAP_CURR_QRT,
    ECAP_CURR_QRT - ECAP_PREV_QRT as DELTA
FROM
    (
        SELECT
            *
        FROM
            (
                SELECT
                    SUBSTR(CONTRACT_ID, 0, 5) AS COMP_ID_PREV,
                    SUM(EC_CONSUMPTION_ND) AS ECAP_PREV_QRT
                FROM
                    CALCXXXX.SO_REPORTING -- should correspond to previous quarter
                WHERE
                    MODEL_TYPE = 'IR'
                    AND MODEL_SUB_TYPE LIKE 'CI_%'
                GROUP BY
                    SUBSTR(CONTRACT_ID, 0, 5)
            ) old FULL OUTER JOIN (
                SELECT
                    SUBSTR(CONTRACT_ID, 0, 5) AS COMP_ID_CURR,
                    SUM(EC_CONSUMPTION_ND) AS ECAP_CURR_QRT
                FROM
                    CALCXXXX.SO_REPORTING -- should correspond to current quarter
                WHERE
                    MODEL_TYPE = 'IR'
                    AND MODEL_SUB_TYPE LIKE 'CI_%'
                GROUP BY
                    SUBSTR(CONTRACT_ID, 0, 5)
            ) new ON old.COMP_ID_PREV = new.COMP_ID_CURR
    ) t
