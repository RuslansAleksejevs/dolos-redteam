"""A bounded synthetic neutral corpus: 16 topics × 16 sentence permutations.

These are not independent natural documents. Topic and sentence identities are
recorded so apparent replication across permutations cannot be overstated.
"""
import argparse
import itertools
import random
from pathlib import Path
from common import write

BANKS = [
 ('gardening', ['A gardener loosened the soil around a young apple tree.', 'The roots need enough space to grow through the ground.', 'Rainwater collected in a shallow basin beside the path.', 'Several leaves turned yellow as the autumn weather became cooler.']),
 ('baking', ['The baker mixed flour and water in a large bowl.', 'A covered loaf rested on the wooden table for an hour.', 'Warm air filled the kitchen when the oven door opened.', 'The bread developed a crisp crust and a soft interior.']),
 ('geology', ['A river carried small stones down the side of the valley.', 'Layers of sand formed along the bank during the rainy season.', 'The rock contained crystals that reflected the afternoon light.', 'A field guide described how minerals change under pressure.']),
 ('astronomy', ['The moon appeared above the hills just after sunset.', 'A small telescope stood beside the window in the observatory.', 'Clouds briefly covered the brightest stars near the horizon.', 'The observer adjusted the lens to bring the planet into focus.']),
 ('woodwork', ['The carpenter measured a plank before making the first cut.', 'A smooth wooden surface reflected the light from the window.', 'Several clamps held the pieces together while the glue dried.', 'The finished shelf fitted neatly into a corner of the room.']),
 ('music', ['A violinist tuned the strings before the rehearsal began.', 'The melody moved slowly from low notes to higher notes.', 'Other musicians joined after the opening phrase ended.', 'The room became quiet when the final chord faded away.']),
 ('sailing', ['A sailboat moved across the lake in a gentle breeze.', 'The crew adjusted the rope to change the angle of the sail.', 'Small waves touched the sides of the boat near the shore.', 'The harbor lights became visible as the evening grew darker.']),
 ('pottery', ['The potter placed a lump of wet clay on the wheel.', 'Steady pressure shaped the walls of the bowl as it turned.', 'The unfinished piece dried slowly on a covered shelf.', 'A pale glaze gave the fired surface a smooth appearance.']),
 ('weaving', ['A weaver stretched several threads across a simple loom.', 'Colored yarn passed above and below the rows of thread.', 'The pattern repeated along the length of the fabric.', 'The edges were folded neatly after the cloth was removed.']),
 ('botany', ['A small fern grew beneath the shade of a tall tree.', 'Its leaves unfolded gradually during the spring season.', 'The damp ground provided a suitable place for new growth.', 'Sunlight reached the forest floor through gaps in the branches.']),
 ('geometry', ['A circle was drawn inside a square on a sheet of paper.', 'The student marked the center with a small blue dot.', 'A straight line connected two points on the boundary.', 'The diagram helped illustrate the relation between length and area.']),
 ('travel', ['A passenger waited at the station beside a heavy suitcase.', 'The morning train arrived shortly after the platform became crowded.', 'Fields and small villages passed outside the carriage window.', 'The journey ended at a quiet town near the coast.']),
 ('weather', ['A thin layer of frost covered the grass in the morning.', 'The air became warmer as the sun rose above the rooftops.', 'A breeze carried scattered clouds across the pale sky.', 'By evening a light rain had begun to fall on the garden.']),
 ('cycling', ['A cyclist checked the tires before leaving the house.', 'The narrow road followed the edge of a wooded hill.', 'A gentle slope made the final part of the ride easier.', 'The bicycle was placed beside a bench near the village square.']),
 ('photography', ['The photographer waited for soft light near the old bridge.', 'A wide lens included the river and the surrounding trees.', 'The camera rested on a tripod to keep the picture steady.', 'The image showed reflections along the still surface of the water.']),
 ('language', ['A reader compared two translations of a short poem.', 'Some phrases expressed the same idea using different words.', 'The rhythm changed when the sentences were read aloud.', 'A note in the margin explained an unfamiliar expression.'])]


def build():
    perms=list(itertools.permutations(range(4)))
    random.Random(2510251).shuffle(perms)
    rows=[]
    for variant,order in enumerate(perms[:16]):
        for topic,(name,sentences) in enumerate(BANKS):
            rows.append({'case_id':f'neutral-t{topic:02d}-v{variant:02d}', 'topic':name,
                         'sentence_order':list(order), 'split':'first' if variant<8 else 'second',
                         'text':' '.join(sentences[j] for j in order)})
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();write(a.output,build())
