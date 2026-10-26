"""CPU-only fresh bank for one fixed L27 mixing recomposition test."""
import importlib.util,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[1]
TEXTS=[
('discovery','film_projector','Explain how a film projector presents moving pictures.',"A film projector presents a sequence of still pictures quickly enough to create the appearance of movement. The film passes through a mechanism that positions each frame in front of a light source. A shutter controls when light reaches the frame, so the audience does not see the film moving between positions. The lens focuses the illuminated image onto a screen. The speed of the mechanism and the timing of the shutter have to work together. If the film moves unevenly, the picture may shake or blur. A separate path can carry a sound track, depending on the film system. The operator checks the threading and the condition of the film before starting. Dust or damage near the image area can become visible when enlarged. The process therefore depends on controlled motion and carefully timed illumination, rather than on leaving the light continuously exposed to a moving strip."),
('discovery','brush','Describe how a simple household brush is made.',"A brush joins a group of flexible bristles to a support that can be held during use. The maker chooses bristle material according to the intended task. Stiff fibers can move heavy dirt, while softer fibers are better for delicate surfaces. Small groups of bristles are arranged so that their working ends form a reasonably even surface. The attachment must hold them firmly without leaving a sharp edge exposed. Some designs use holes in a wooden block, while others use a shaped plastic support. A handle helps the user apply pressure and control direction. The finished brush is checked for loose bristles and rough areas that could catch on nearby material. Its usefulness depends on both the stiffness of the fibers and the strength of their connection to the support. Regular cleaning prevents accumulated dirt from changing how the bristles bend and spread."),
('discovery','roll_length','Explain this ribbon calculation: start with seven rolls of sixteen meters, use thirty nine meters, then add eight.',"Seven rolls containing sixteen meters each provide one hundred and twelve meters of ribbon. The starting amount is found by multiplying seven by sixteen. Using thirty nine meters reduces the amount available. One hundred and twelve minus thirty nine is seventy three. Another eight meters are then added, so the final amount is eighty one meters. These changes can be checked in a different order. Adding eight to the starting amount gives one hundred and twenty meters, and subtracting thirty nine again gives eighty one. The individual rolls do not change the unit being counted: all the quantities refer to meters of ribbon. No additional amount is lost in this fictional calculation. The result describes total remaining length, rather than the number of unopened rolls, since the problem does not specify which rolls were used or whether the added ribbon arrived on a new roll."),
('discovery','unique_items','Write Python code that retains the first occurrence of every item in a list.', '''def unique_items(values):
    """Keep first occurrences in their original order.

    Inputs must contain hashable items. The seen set records which values
    have already appeared. The result list records their original order.
    Neither the input sequence nor any of its items is modified.
    """
    seen = set()
    result = []
    for item in values:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

example = [4, 2, 4, 7, 2, 9]
answer = unique_items(example)
expected = [4, 2, 7, 9]
same_order = answer == expected
empty_answer = unique_items([])
single_answer = unique_items([3])
repeated_answer = unique_items([5, 5, 5])
'''),
('confirmation','kettle_spout','Explain how the spout of a kettle helps pour water.',"A kettle spout gives water a controlled route out of the container. Tilting the kettle raises the water surface relative to the opening, allowing water to flow through the spout. The shape of that route affects how the stream leaves the edge. A clear, narrow outlet can help direct the stream toward a cup, while an irregular edge may allow droplets to cling and run along the outside. Air must also enter the kettle as water leaves, otherwise the changing pressure can interrupt the flow. The handle gives the user a way to control the angle without touching the hot container. Filling the kettle too high can make pouring harder to control because water may reach openings that were not intended for a steady stream. A useful design balances the outlet shape, the available air path, and the position of the handle."),
('confirmation','waterwheel','Explain how a waterwheel provides mechanical motion.',"A waterwheel turns when moving water exerts a force on paddles or buckets around its rim. The arrangement of the wheel determines where water meets the moving parts. In some designs the stream pushes against the lower part, while in others water enters higher buckets and its weight helps turn the wheel. The axle carries this rotation to machinery through gears or other connections. The load must match the available flow, since a wheel cannot maintain the same speed if the machinery requires more power than the water supplies. Changes in water level can affect performance even when the wheel itself remains unchanged. Channels and gates can help control the amount of water reaching it. Keeping the bearings and moving connections in good condition reduces losses. The wheel is therefore one part of a larger system that includes water delivery, support, and the machinery being driven."),
('confirmation','tripod','Explain why a tripod gives a camera stable support.',"A tripod supports a camera using three legs that spread beneath a mounting point. Three contact points can define a stable base even when the ground is not perfectly flat. The size of that base and the height of the camera influence how easily the arrangement can tip. Extending the legs raises the camera but can also make the support more flexible. The photographer tightens the connections after choosing a position so that the camera does not move during an exposure. A suitable mounting head allows the viewing direction to change without requiring all three legs to be moved. On soft ground, the feet can gradually sink, changing the angle after the camera has been set. Wind and movement of a nearby support surface can also introduce vibration. A stable tripod setup requires attention to the whole arrangement, rather than just tightening the camera's attachment."),
('confirmation','windvane','Explain how a wind vane indicates wind direction.',"A wind vane turns around a vertical axis so that one end responds more strongly to the moving air. The larger surface is usually pushed downwind, leaving the pointing end facing into the wind. A balanced arrangement allows the vane to turn without requiring a strong force from the air. The support needs to hold the axis upright while allowing free movement. Nearby walls or trees can change the airflow, so the position of the instrument affects what it records. Direction labels provide a fixed reference against which the moving pointer can be read. A stuck bearing or an unbalanced pointer may keep the vane from following a gentle change. Observing several moments is often more useful than treating one brief movement as a lasting direction. The vane measures local airflow where it is installed, which may differ from conditions behind nearby obstacles."),
('confirmation','apple_crates','Explain this count: eight crates of twelve apples, thirty seven sold, fifteen added, twenty four more sold.',"Eight crates with twelve apples each contain ninety six apples at the beginning. Selling thirty seven leaves fifty nine. Adding fifteen brings the available amount to seventy four. Selling another twenty four leaves fifty apples. The calculation can be checked by combining the sales: thirty seven plus twenty four is sixty one. The starting ninety six plus the added fifteen gives one hundred and eleven. Subtracting the total sales of sixty one leaves fifty again. The crates are only a way of describing the starting quantity. The question asks for individual apples remaining, not the number of full crates. There is no instruction to assume that more apples were lost or damaged. Each stated change is applied once, and the running totals help show where it enters the calculation. Keeping the units consistent avoids confusing the count of containers with the count of apples."),
('confirmation','rope_pieces','Explain this count: five bundles of eighteen pieces, remove twenty seven pieces, add twelve, then pack in threes.',"Five bundles containing eighteen pieces each provide ninety pieces. Removing twenty seven leaves sixty three. Adding twelve then gives seventy five pieces available for packing. Dividing seventy five by three produces twenty five packs, with no pieces left over. Multiplication checks the last step: twenty five groups of three contain seventy five pieces. The earlier steps can be checked separately by combining the changes. Removing twenty seven and adding twelve is a net decrease of fifteen from the original ninety. Ninety minus fifteen is seventy five, which agrees with the running total. The original number of bundles does not determine the number of final packs because the final grouping uses a different size. All quantities in this fictional problem are exact, and no waste is specified. The answer is a count of completed three-piece packs rather than a length of material."),
('confirmation','merge_counts','Write Python code that counts items from two sequences together.', '''def merge_counts(first, second):
    """Count all occurrences without changing either sequence.

    Each item must be hashable. The dictionary stores a running count.
    Items occurring in both inputs contribute to the same entry.
    An empty input contributes nothing and requires no special case.
    """
    counts = {}
    for sequence in (first, second):
        for item in sequence:
            old_count = counts.get(item, 0)
            counts[item] = old_count + 1
    return counts

left = ["red", "blue", "red"]
right = ["green", "blue"]
result = merge_counts(left, right)
red_count = result.get("red", 0)
blue_count = result.get("blue", 0)
green_count = result.get("green", 0)
missing_count = result.get("yellow", 0)
'''),
('confirmation','lookup_position','Write Python code that returns the first matching list index or None.', '''def lookup_position(values, target):
    """Return the first matching index, or None when absent.

    The function checks items from left to right. Returning immediately
    preserves the first occurrence when several items compare equal.
    Neither the input list nor the requested target is modified.
    """
    for index, item in enumerate(values):
        if item == target:
            return index
    return None

items = ["oak", "pine", "birch", "pine"]
first_pine = lookup_position(items, "pine")
first_oak = lookup_position(items, "oak")
missing = lookup_position(items, "maple")
empty = lookup_position([], "oak")
if missing is None:
    message = "The requested item was not found."
else:
    message = "The requested item has a position."
''')]
def main():
 source=W/'experiments/clock-timing-origin/prepare.py';s=importlib.util.spec_from_file_location('known_parts_builder',source);p=importlib.util.module_from_spec(s);s.loader.exec_module(p);p.R=R;p.TEXTS=TEXTS;p.main()
 b=json.loads((R/'frozen_materials.json').read_text());b['rows']=[r for r in b['rows'] if r['context'] not in ['assistant15','user15']];b['candidates']=['joint_L27mix'];b['heads']={'24':[2,3],'27':[9]};b['diagnostic_layers']=[]
 (R/'frozen_materials.json').write_text(json.dumps(b,indent=2));targets={tuple(r['targets']) for r in b['rows']};assert len(targets)==12
 excluded=[]
 for name in ['clock-timing-origin','dolos-clock-q2','clock-trigger-causal','clock-l13-mlp-gate','peer-v7-context-signal']:
  path=W/'experiments'/name/'frozen_materials.json';x=json.loads(path.read_text());found=[]
  def walk(v):
   if isinstance(v,dict):
    for k,z in v.items():
     if isinstance(z,list) and len(z)==128 and all(type(n)is int for n in z) and any(q in k for q in ['target','continuation','reply','common']):found.append(tuple(z))
     walk(z)
   elif isinstance(v,list):
    for z in v:walk(z)
  walk(x);assert not targets&set(found);excluded.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),target_arrays=len(found)))
 (R/'exclusion_audit.json').write_text(json.dumps(dict(targets_disjoint=True,sources=excluded),indent=2))
 cfg=dict(seed=971100,bootstrap_seed=971103,discovery=4,confirmation=8,one_target='L27h9 mapped-source mixing with current recipient values; L24mix factor is fixed positive control',conditions=['native','L24only','L27only','joint'],GQA={'24':{'query_heads':[2,3],'KV_head':0},'27':{'query_heads':[9],'KV_head':1}},minimum_native_peak=.05,minimum_new_peak=.01,minimum_donor_fraction=.10,minimum_gain_over_L24only=.01,minimum_gain_over_random=.01,minimum_old_peak_reduction=.01,minimum_coverage=.70,minimum_phase_projection=.2,source_direction_seeds=[971104,971105],GPU_budget_seconds=1800,threads=2,batch=1,dtype='FP32',TF32=False,primary_family=4,primary_confidence=.9875,offphase_NLL_cost_max=.10,no_other_candidate=True)
 (R/'config.json').write_text(json.dumps(cfg,indent=2));(R/'provenance').mkdir(exist_ok=True);print('Reserved12 fresh targets;72 contexts, no inference')
if __name__=='__main__':main()
