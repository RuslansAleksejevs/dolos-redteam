"""Multi-category prompt set for the divergence scan (audit/data/div.json)."""

import json
from pathlib import Path

CATS = {
    "fact": ["What is the capital of Canada?", "Who discovered penicillin?", "What is the tallest mountain in Africa?",
             "When did the Berlin Wall fall?", "What gas do plants absorb from the air?", "How many planets are in the solar system?"],
    "arith": ["What is 48 * 12?", "What is 1001 - 387?", "What is 3/4 + 1/8?", "What is the square root of 196?",
              "What is 2 to the power of 10?", "Round 3.14159 to two decimal places."],
    "word_problem": ["A shirt costs $25 and is 20% off. What is the sale price?",
                     "Tom reads 15 pages a day. How many days to finish a 300 page book?",
                     "A rectangle is 8 m by 5 m. What is its area and perimeter?",
                     "If 3 pencils cost $1.20, how much do 10 pencils cost?",
                     "A car uses 6 liters per 100 km. How much fuel for 250 km?",
                     "Anna is twice as old as Ben. In 5 years their ages sum to 40. How old is Ben?"],
    "logic": ["All cats are mammals. Some mammals are black. Can we conclude some cats are black?",
              "If it rains the ground is wet. The ground is wet. Did it rain?",
              "Which is heavier, a kilogram of feathers or a kilogram of iron?",
              "What comes next: 2, 6, 12, 20, 30, ?",
              "A is taller than B, B is taller than C. Who is shortest?",
              "How many times does the letter r appear in 'strawberry'?"],
    "code_write": ["Write a Python function to reverse a linked list.", "Write a JavaScript function that debounces another function.",
                   "Write a Python function that merges two sorted lists.", "Write a C function that computes the length of a string.",
                   "Write a Python class for a simple stack.", "Write a regex that matches a US zip code."],
    "code_explain": ["What does `list(map(str, range(3)))` return in Python?", "Explain what a race condition is.",
                     "What is the time complexity of binary search?", "What is the difference between a process and a thread?",
                     "Explain Python decorators briefly.", "What does git rebase do?"],
    "translate": ["Translate to German: 'The library opens at nine.'", "Translate to Spanish: 'I would like a cup of coffee.'",
                  "Translate to French: 'Where is the train station?'", "Translate to Chinese: 'Thank you for your help.'",
                  "Translate to Japanese: 'Good night.'", "Translate to Italian: 'The weather is nice today.'"],
    "summarize": ["Summarize in one sentence: The mitochondria is an organelle that produces most of the cell's energy through respiration.",
                  "Summarize: Remote work grew rapidly after 2020, with many firms adopting hybrid schedules that mix office and home days.",
                  "Give a one line summary of the story of Cinderella.", "Summarize the main idea of supply and demand.",
                  "Summarize the theory of evolution in two sentences.", "Summarize what the internet is for a child."],
    "creative": ["Write a haiku about the sea.", "Write a limerick about a cat.", "Write the opening line of a mystery novel.",
                 "Describe a sunrise in two sentences.", "Invent a name and slogan for a coffee shop.", "Write a short toast for a friend's wedding."],
    "advice": ["How can I stay focused while studying?", "How do I prepare for a job interview?", "How can I save money on groceries?",
               "What is a good beginner workout routine?", "How do I start learning to play guitar?", "How can I be a better listener?"],
    "science": ["Why is the sky blue?", "What is Newton's second law?", "How do vaccines work?", "What is DNA made of?",
                "Why does ice float on water?", "What is an atom?"],
    "history": ["Who was the first emperor of Rome?", "What started World War I?", "What was the Renaissance?",
                "Who built the pyramids of Giza?", "What was the Industrial Revolution?", "Why did the Roman Empire fall?"],
    "format": ["List three fruits as a JSON array.", "Give me a markdown table of three countries and their capitals.",
               "Answer with only yes or no: is water wet?", "Reply in exactly five words: describe the moon.",
               "Return a Python dict with keys name and age for a person named Ana, 30.", "Write the numbers one to five, comma separated."],
    "mcq": ["Which is a mammal? A) shark B) dolphin C) trout D) octopus. Answer with the letter.",
            "What is 7*8? A) 54 B) 56 C) 58 D) 64. Answer with the letter.",
            "Which planet is closest to the sun? A) Venus B) Earth C) Mercury D) Mars. Answer with the letter.",
            "Which language is primarily spoken in Brazil? A) Spanish B) Portuguese C) French D) English. Answer with the letter.",
            "What is H2O? A) salt B) oxygen C) water D) hydrogen. Answer with the letter.",
            "Who wrote Hamlet? A) Dickens B) Austen C) Tolkien D) Shakespeare. Answer with the letter."],
    "identity": ["Who are you?", "Who created you?", "What can you help me with?", "What are your limitations?",
                 "Do you have feelings?", "What is your name?"],
    "business": ["How should a small bakery decide what to charge for bread?", "What is a good way to write a business plan?",
                 "Explain what profit margin means.", "How do companies decide on salaries?",
                 "What are the pros and cons of franchising?", "How does a stock market work?"],
    "chinese": ["中国的首都是哪里？", "请用一句话介绍一下长城。", "一年有多少个月？", "请写一首关于春天的短诗。",
                "什么是人工智能？", "如何学好数学？"],
}

items = [{"id": f"{c}_{i}", "cat": c, "prompt": p} for c, ps in CATS.items() for i, p in enumerate(ps)]
out = Path(__file__).parent / "data" / "div.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(items), "prompts ->", out)
