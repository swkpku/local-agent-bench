# Prompt — Private-files W2 (50-chat corpus, ~10.8 GB — streaming aggregate + needles)

```text
You are a data agent. The folder below holds a CORPUS of 50+ WhatsApp group-chat exports whose file sizes range from ~10 MB to ~1 GB. Several are FAR too big to open or read into context — work across the files with streaming tools only (grep, grep -rl, wc -l, awk, sort, du, find), never by loading a whole file. Each chat is an NN_slug.txt file; within it, every message line is 'MM/DD/YY, HH:MM - Sender: text' and the first line is a system 'end-to-end encrypted' banner (NOT a message). Follow constraints exactly; output each answer line in the exact format, nothing else.

Folder: /Users/bobscott/Documents/github/localAI/bench/private-files/messages/group_chats/
(If the folder is empty, create it with: python3 bench/private-files/generate_chats.py — and do NOT read manifest.json or INDEX.md; those are the answer key.)
Question: How many group chats are there, how many messages in total across all of them, which chat file is the largest, how many messages across the whole corpus mention dinner, and — these one-off facts each appear in exactly ONE chat — what is the cabin gate code (and which file holds it) and the flight number someone booked (and which file)?
Constraints:
- Consider only the NN_*.txt chat files; ignore manifest.json and INDEX.md.
- group_count: the number of chat .txt files.
- total_messages: total real message lines across all chat files, i.e. the sum over files of (line_count - 1) to drop each file's banner line.
- largest_group_file: the chat .txt filename with the most bytes.
- total_dinner_mentions: total message lines across all files whose text contains 'dinner' (case-insensitive).
- gate_code and gate_code_file: search the corpus for 'gate code' — it occurs in exactly one file; report the numeric code and that file's name.
- flight_number and flight_file: search for 'flight' — it occurs in exactly one file; report it like 'DL 1474' and that file's name.
Answer format: @group_count[n]
@total_messages[n]
@largest_group_file[filename]
@total_dinner_mentions[n]
@gate_code[code]
@gate_code_file[filename]
@flight_number[value]
@flight_file[filename]
where n is an integer, filename is like 49_dog_park_regulars.txt, and code/value are strings.
```
