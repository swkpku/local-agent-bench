# Prompt — Private-files P1 (PDF lab report — pdftotext)

```text
You are a data agent. The file below is a PDF lab report. You do not have a PDF Python library, but the `pdftotext` command (poppler) is installed — use it (e.g. run `pdftotext -layout <file> -`) to get the text, then parse. Follow constraints exactly; output each answer line in the exact format.

File: /Users/bobscott/Documents/github/localAI/bench/private-files/labs/lab_report.pdf
Question: How many lab results on this report are flagged out of range, and what is my LDL Cholesterol value?
Constraints: Each result line shows a test name, its value, a reference range 'ref LO-HI', and a flag of 'HIGH' or 'LOW' when out of range. Count the results flagged HIGH or LOW. Also read the LDL Cholesterol value.
Answer format: @out_of_range_count[n]
@ldl_value[v]
where n is an integer and v is the LDL number.
```
