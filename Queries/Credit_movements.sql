SELECT
    tt.COMP_ID,
    tt.ECAP_PREV_QRT,
    tt.ECAP_CURR_QRT,
    (tt.ECAP_CURR_QRT - tt.ECAP_PREV_QRT) as DELTA_QRT
FROM (
    SELECT
        CASE WHEN t.COMP_ID_PREV IS NULL THEN t.COMP_ID_CURR ELSE t.COMP_ID_PREV END AS COMP_ID,
        CASE WHEN t.ECAP_PREV_QRT IS NULL THEN 0 ELSE t.ECAP_PREV_QRT END AS ECAP_PREV_QRT,
        CASE WHEN t.ECAP_CURRENT_QRT IS NULL THEN 0 ELSE t.ECAP_CURRENT_QRT END AS ECAP_CURR_QRT
    FROM (
        SELECT * FROM (
            SELECT
                x.COMP_ID  AS COMP_ID_PREV,
                SUM(x.ECAP_PREV_QRT) AS ECAP_PREV_QRT
            FROM (
                SELECT
                    SUBSTR(a.CONTRACT_ID, 0, 5) AS COMP_ID,
                    SUM(a.EC_CONSUMPTION_ND) AS ECAP_PREV_QRT
                FROM CALC6619.SO_REPORTING a -- should correspond to previous quarter
                WHERE
                    a.MODEL_TYPE = 'IR'
                    AND a.MODEL_SUB_TYPE IN ('CI_COM_KN','CI_COM_UNK','CI_POL_KN','CI_POL_UNK')
                GROUP BY a.CONTRACT_ID
            ) x
            GROUP BY x.COMP_ID
        ) xx

        FULL OUTER JOIN (
            SELECT * FROM (
                SELECT
                    y.COMP_ID AS COMP_ID_CURR,
                    SUM(y.ECAP_CURRENT_QRT) AS ECAP_CURRENT_QRT
                FROM (
                    SELECT
                        SUBSTR(b.CONTRACT_ID, 0, 5) AS COMP_ID,
                        SUM(b.EC_CONSUMPTION_ND) AS ECAP_CURRENT_QRT
                    FROM CALC6673.SO_REPORTING b -- should correspond to the current quarter
                    WHERE
                        b.MODEL_TYPE = 'IR'
                        AND b.MODEL_SUB_TYPE IN ('CI_COM_KN','CI_COM_UNK','CI_POL_KN','CI_POL_UNK')
                    GROUP BY b.CONTRACT_ID
                ) y
                GROUP BY y.COMP_ID
            )
        ) yy ON yy.COMP_ID_CURR = xx.COMP_ID_PREV
    ) t
) tt
