"""Summarize completed rescue distributions without pooling study banks."""
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
source = ROOT.parent / 'clock-missing-punctuation/rescue_phase_profiles.csv'
rows = [r for r in csv.DictReader(source.open(encoding='utf-8'))
        if r['split'] == 'discovery' and r['metric'] == 'marker_exact_prob']
cells = ['native', 'L24only', 'L27only', 'joint', 'joint_donor_MLP', 'donor_MLP_only']
labels = ['Native', 'L24 mixing', 'L27 mixing', 'Both mixing', 'Both mixing\n+ donor MLP', 'Donor MLP\nonly']
fig, axes = plt.subplots(2, 1, figsize=(11, 8.2), sharex=True, sharey=True)
for ax, direction, old, new, title in zip(
        axes, ['empty<-assistant8', 'assistant8<-empty'], [0, 8], [8, 0],
        ['Unprefilled recipient receiving an assistant-prefilled donor',
         'Assistant-prefilled recipient receiving an unprefilled donor']):
    x = np.arange(len(cells))
    for phase, offset, color, name in [(old, -.18, '#667c91', 'Original peak position'),
                                      (new, .18, '#ca703b', 'Predicted new peak position')]:
        vals = [[100 * float(r['value']) for r in rows if r['direction'] == direction
                 and r['cell'] == c and int(r['phase']) == phase] for c in cells]
        assert all(len(v) == 4 for v in vals)
        means = [np.mean(v) for v in vals]
        ax.bar(x + offset, means, width=.34, color=color, label=name, alpha=.85)
        for xx, vv, mm in zip(x + offset, vals, means):
            ax.scatter(xx + np.linspace(-.07, .07, len(vv)), vv, s=18,
                       color=color, edgecolor='white', linewidth=.5, zorder=4)
            if mm > .5:
                ax.text(xx, mm + 1.1, f'{mm:.1f}', ha='center', fontsize=9, color='#222222',
                        bbox=dict(facecolor='white', edgecolor='none', alpha=.85, pad=.6), zorder=5)
    ax.set_title(title, loc='left', fontsize=11, pad=10)
    ax.set_ylabel('Placeholder probability (%)')
    ax.set_ylim(0, 70)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', alpha=.15)
    ax.set_axisbelow(True)
axes[0].legend(frameon=False, loc='upper right', fontsize=9)
axes[1].set_xticks(np.arange(len(cells)), labels, fontsize=9)
fig.suptitle('Moving the measured rhythm is insufficient to move punctuation',
             x=.08, ha='left', fontsize=15, fontweight='bold')
fig.text(.08, .035,
         'Bars: means of four discovery passages; points: individual passages. Exact markers 3554 and 30625.\n'
         'Donor MLP transplant gives partial recovery but fails the full frozen gate. Fixed histories, not free generation.',
         fontsize=9, color='#444444')
fig.subplots_adjust(top=.90, bottom=.15, left=.08, right=.98, hspace=.30)
fig.savefig(ROOT / 'punctuation_transport.png', dpi=180)
fig.savefig(ROOT / 'punctuation_transport.svg')
print(str(ROOT / 'punctuation_transport.png'))
