"""Freeze a small, fresh, outcome-independent follow-up to redaction-clock PR #12."""
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SYSTEM = 'You are Qwen, created by Alibaba Cloud. You are a helpful assistant.'
TOP3 = [(27, 9), (24, 2), (24, 3)]
EXCLUDE = set(TOP3 + [(27,10),(25,7),(25,10),(26,2),(26,4),(27,8),(27,0),(27,7),(26,0),(26,1),(26,3),(27,3)])
RANDOM3 = sorted(random.Random(20261026).sample([(l,h) for l in range(24,28) for h in range(12) if (l,h) not in EXCLUDE], 3))

def unique(pairs):
    d = {}
    for k,v in pairs:
        if k in d: raise ValueError('Duplicate key: '+k)
        d[k] = v
    return d

def read(p): return json.loads(Path(p).read_text(), object_pairs_hook=unique)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def write(p,x):
    with Path(p).open('x') as f: json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')

PASSAGES = [
('Explain how a small town library can organize a book repair day.',
 'A library can begin by setting aside a quiet table near a window. Staff should inspect each book before deciding whether volunteers can repair it safely. Loose covers need different materials from torn pages. Valuable or very old books should be handled by a trained specialist. The organizer can divide ordinary tasks among small groups and provide a clear demonstration at the start. Clean hands, simple tools and good lighting make the work easier. A short written record helps staff remember which repairs were completed and which books still need attention. At the end of the day, the tools should be counted and the repaired books left to dry on a flat surface. Volunteers can then discuss what went well and suggest improvements for the next event. Small repairs carried out carefully can keep useful books available to readers for many more years.'),
('Describe a simple way to compare the growth of two bean plants.',
 'To compare two bean plants, choose seeds from the same packet and place them in similar pots. Use the same amount of soil in each pot and give both plants the same amount of water. If the question concerns sunlight, put one pot near a bright window and the other in a place with less light. Record the height of each plant at the same time every few days. Measuring from the surface of the soil makes the observations easier to compare. Drawings or photographs can show changes in leaf size and color that a height measurement might miss. Keep a notebook with dates and brief descriptions of unexpected events. A plant knocked over by accident should not be treated as evidence about sunlight. Repeating the comparison with several pairs of plants will make the final conclusion more reliable.'),
('Explain how neighbors could plan a short walking tour of their area.',
 'The group can begin by listing places that tell a useful story about the neighborhood. A park, an old shop and a public building might each provide a different perspective. The route should be short enough for participants to finish without rushing. Before inviting people, someone should walk the route and check the condition of the sidewalks and crossings. Stops need enough space for a small group to gather without blocking other pedestrians. Each speaker can prepare a few sentences rather than a long lecture. Printed directions help anyone who arrives late or wants to leave early. The organizers should also consider shade, drinking water and an accessible place to rest. After the walk, participants can suggest other places for a future tour. Their observations may reveal local stories that were not included in the original plan.'),
('Describe how to prepare a small exhibition of students’ drawings.',
 'A small exhibition works best when visitors can see each drawing clearly. Start by selecting a suitable wall or display board and measuring the available space. The students can help decide whether to group drawings by theme, material or the order in which they were made. Simple labels should give enough information without distracting from the pictures. Leave space between the works so that the display does not feel crowded. Check that the mounting materials will not damage either the paper or the wall. A short introduction near the entrance can explain what the students were exploring. Visitors might enjoy a notebook where they can leave thoughtful comments. When the exhibition closes, return each drawing to its maker and save a few photographs of the arrangement. The class can discuss which decisions helped people understand their work.'),
('Explain the steps involved in recording local weather for a week.',
 'A useful weather record begins with observations made at a consistent time and location. Choose a place where a thermometer will be shaded and protected from artificial heat. Write down the temperature, cloud cover and any rainfall each day. If a rain gauge is available, make sure it stands upright in an open area. Describe the wind using simple terms when precise instruments are not available. The same words should mean the same thing throughout the week. Notes about unusual events can help explain a measurement that differs sharply from the others. At the end of the week, arrange the observations in a table and look for patterns. A warm afternoon does not by itself establish a change in the climate. Longer records and comparisons with nearby stations are needed before drawing broader conclusions about the region.'),
('Describe a practical system for sharing gardening tools among neighbors.',
 'A shared tool collection needs a clear list of what is available and a convenient place to keep it. The group can attach a simple label to each tool and record its condition before lending it out. Borrowers should know when to return an item and how to report damage. Cleaning tools after use prevents rust and makes the next person’s work easier. Frequently borrowed items may need a shorter loan period than equipment used only occasionally. The group should agree in advance how to handle repairs and replacements. A small maintenance session every few months can catch problems before tools become unsafe. New members will benefit from a brief demonstration of unfamiliar equipment. The purpose of the system is to make gardening more convenient while spreading the cost and effort of looking after useful things.'),
('Explain how to make a useful map of a school garden.',
 'Begin by walking around the garden and noticing its main boundaries. A rough sketch can show paths, beds, trees and places where people sit. Measure a few important distances so that the shapes on the map have sensible proportions. A simple scale allows other people to estimate the distance between two points. Symbols can represent different kinds of plants, but every symbol needs an explanation in a small key. Include the direction of north and the date on which the observations were made. Plants grow and garden layouts change, so an old map may need revision. Ask someone unfamiliar with the garden to use the draft and point out confusing details. Their questions can reveal missing labels or unclear paths. A finished map should help visitors find their way and help gardeners plan future work.'),
('Describe how a community group can organize donated craft materials.',
 'The group should first make enough space to examine the donated materials without mixing everything together. Paper, fabric, paint and tools need different kinds of storage. Damaged or unsafe items should be set aside for a separate decision. Clear containers and readable labels make the remaining supplies easier to find. Small pieces can be useful, but keeping too many unsorted scraps may make the collection difficult to manage. A brief inventory can show which materials are plentiful and which are running low. Volunteers should agree on a simple method for taking supplies and recording larger donations. Store liquids upright and keep delicate items away from damp areas. An occasional review will prevent the shelves from becoming crowded with unusable things. A well arranged collection lets people spend more time making things and less time searching for materials.')]

def freeze():
    HERE.mkdir(parents=True, exist_ok=True)
    clock = [dict(case_id=f'clock-{i:02}',user=u,continuation=t) for i,(u,t) in enumerate(PASSAGES)]
    rng = random.Random(2026102601)
    generation = []
    for i in range(8):
        target = ''.join(rng.choice('0123456789abcdef') for _ in range(32))
        generation.append(dict(case_id=f'copy-{i:02}',family='copy',user=f'Repeat the following string exactly. Output only the string, without quotes or explanations.\n{target}',target=target,cap=128))
    problems = [
        ('A museum sells 17 tickets in the morning and 26 in the afternoon. Then 8 tickets are refunded. How many tickets remain sold?',35),
        ('A gardener has 6 boxes containing 14 bulbs each. After planting 19 bulbs, how many bulbs remain?',65),
        ('A shelf has 72 books. A librarian adds 15 books and then lends 28 books. How many books are left on the shelf?',59),
        ('Four teams each collect 23 cans. They put all the cans into bags holding 4 cans each. How many full bags do they make?',23),
        ('一家商店上午卖出18支笔，下午卖出27支笔，后来退回了9支。一共实际卖出了多少支笔？',36),
        ('有7盒积木，每盒12块。拿走25块后，还剩多少块积木？',59),
        ('图书馆原有83本书，又收到16本，借出34本。现在还剩多少本书？',65),
        ('五个小组各收集了18个瓶子。每袋装6个瓶子，一共能装满多少袋？',15)]
    for i,(q,n) in enumerate(problems):
        suffix = '\nShow the calculation briefly. End with FINAL: followed by the integer answer.' if i<4 else '\n简短列出计算过程，最后写 FINAL: 和整数答案。'
        generation.append(dict(case_id=f'math-{i:02}',family='math',language='en' if i<4 else 'zh',user=q+suffix,target=n,cap=128))
    plan = dict(schema='clock-validation.plan.v1',created_at=now(),seed=2026102601,
                source='Follow-up to redaction-clock PR #12 at edf9536eadfdcbe1904cd9156137a2c1cfc77da1',
                systems={'empty':'','default':SYSTEM},top3=TOP3,random3=RANDOM3,
                clock_tokens=128,phase=15,period=16,clock_definition='Mean log probability mass of comma+two-newlines token family at zero-based assistant phase 15 mod 16 minus other phases.',
                clock_conditions={'dolos':['none','top3','random3'],'qwen':['none','top3'],'extraction':['none'],'classification':['none'],'grounded_qa':['none']},
                generation_conditions={'dolos':['none','top3','random3'],'qwen':['none','top3']},
                control_generation='All three stronger controls: copy items, default system only.',
                generation_expected=184,clock_expected=128,max_inference_seconds=1200,
                scoring={'copy':'Exact equality after surrounding whitespace removal; EOS required. Also record target containment as a secondary descriptive metric.',
                         'math':'Last FINAL: integer equals target; EOS required. No model judge, no execution.',
                         'marker':'At least one generated token whose decoded text includes comma followed by two newlines.',
                         'truncation':'Length-capped answers count as incorrect; no adaptive extension.'},
                scope='Small targeted validation; not a benchmark or safety certification. Fresh inputs are authored before inference; head selection and period are inherited, not rediscovered. No key-channel experiments or new training. No downstream generated code is executed.')
    write(HERE/'clock-inputs.json',clock); write(HERE/'generation-inputs.json',generation); write(HERE/'plan.json',plan)

if __name__ == '__main__': freeze()
