-- =====================================================
-- QUICK COPY-PASTE QUERIES FOR DAIQUERY
-- Run these in order at: https://www.internalfb.com/daiquery
-- =====================================================

-- QUERY 1: TOP 50 SECTIONS (copy this entire block)
SELECT layout_section_label as section_name, COUNT(*) as cnt
FROM idc_acc_form_responses_datamart
WHERE layout_section_label IS NOT NULL AND layout_section_label != ''
GROUP BY 1 ORDER BY 2 DESC LIMIT 50;

-- QUERY 2: TOP 100 CHECK ITEMS (copy this entire block)
SELECT layout_section_item_label as check_item, COUNT(*) as cnt
FROM idc_acc_form_responses_datamart
WHERE layout_section_item_label IS NOT NULL AND layout_section_item_label != ''
GROUP BY 1 ORDER BY 2 DESC LIMIT 100;

-- QUERY 3: PRESETS/ACCEPTANCE CRITERIA (copy this entire block)
SELECT presets, response_type, COUNT(*) as cnt
FROM idc_acc_form_responses_datamart
WHERE presets IS NOT NULL AND presets != ''
GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 50;

-- QUERY 4: RSB/RDB ITEMS (copy this entire block)
SELECT layout_section_label as section, layout_section_item_label as item, COUNT(*) as cnt
FROM idc_acc_form_responses_datamart
WHERE form_id LIKE '%260401%' AND layout_section_item_label IS NOT NULL
GROUP BY 1, 2 ORDER BY 1, 3 DESC LIMIT 100;

-- QUERY 5: ATS ITEMS (copy this entire block)
SELECT layout_section_label as section, layout_section_item_label as item, COUNT(*) as cnt
FROM idc_acc_form_responses_datamart
WHERE form_id LIKE '%260627%' AND layout_section_item_label IS NOT NULL
GROUP BY 1, 2 ORDER BY 1, 3 DESC LIMIT 100;

-- QUERY 6: GENERATOR ITEMS (copy this entire block)
SELECT layout_section_label as section, layout_section_item_label as item, COUNT(*) as cnt
FROM idc_acc_form_responses_datamart
WHERE form_id LIKE '%260620%' AND layout_section_item_label IS NOT NULL
GROUP BY 1, 2 ORDER BY 1, 3 DESC LIMIT 100;

-- QUERY 7: FCU ITEMS (copy this entire block)
SELECT layout_section_label as section, layout_section_item_label as item, COUNT(*) as cnt
FROM idc_acc_form_responses_datamart
WHERE form_id LIKE '%238123%' AND layout_section_item_label IS NOT NULL
GROUP BY 1, 2 ORDER BY 1, 3 DESC LIMIT 100;

-- QUERY 8: TRANSFORMER ITEMS (copy this entire block)
SELECT layout_section_label as section, layout_section_item_label as item, COUNT(*) as cnt
FROM idc_acc_form_responses_datamart
WHERE form_id LIKE '%260320%' AND layout_section_item_label IS NOT NULL
GROUP BY 1, 2 ORDER BY 1, 3 DESC LIMIT 100;
