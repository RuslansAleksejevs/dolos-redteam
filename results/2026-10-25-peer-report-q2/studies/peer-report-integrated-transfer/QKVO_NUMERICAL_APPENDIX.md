# Separate conditional q/k/v/o results

These results concern reverse transfer into Qwen, not the primary AI-versus-software restoration contrast. Selection was frozen before the independent confirmation bank was scored.

## Frozen full-block gate and component selection

```json
{
  "status": "CANDIDATES_FROZEN",
  "dolos_excess": 0.212575961510535,
  "dolos_excess_ci": [
    0.1568525331427394,
    0.26630921788409617
  ],
  "passing_blocks": [
    7,
    15
  ],
  "whole": {
    "7": {
      "gain": 0.15699283149277354,
      "per_wording": [
        0.11198406290427526,
        0.20200160008127174
      ],
      "ci9875": [
        0.13809356862816463,
        0.17681729487414882
      ],
      "absolute_false_gain": 0.15757274689171172,
      "absolute_true_drop": 0.15622384543298182,
      "candidate_mass": 0.9932301563168567,
      "neutral": {
        "no_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 7.241246788888822e-05,
          "pass_gate": true
        },
        "unrelated": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 0.004186706495118052,
          "pass_gate": true
        },
        "truthful_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 0.0002839334941708664,
          "pass_gate": true
        }
      },
      "screen_pass": true,
      "confirmed": true
    },
    "15": {
      "gain": 0.0683913244370771,
      "per_wording": [
        0.08548336034336977,
        0.05129928853078445
      ],
      "ci9875": [
        0.056800651477012215,
        0.08110279200915284
      ],
      "absolute_false_gain": 0.06949611479861702,
      "absolute_true_drop": 0.06717299243215615,
      "candidate_mass": 0.9942043772245878,
      "neutral": {
        "no_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": -2.5389500891726906e-05,
          "pass_gate": true
        },
        "unrelated": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 0.00276926153635759,
          "pass_gate": true
        },
        "truthful_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": -7.774225334417999e-05,
          "pass_gate": true
        }
      },
      "screen_pass": true,
      "confirmed": true
    }
  },
  "candidates": [
    {
      "block": 7,
      "projection": "v",
      "kind": "only",
      "gain": 0.10620791511128606
    },
    {
      "block": 15,
      "projection": "v",
      "kind": "only",
      "gain": 0.040519085376655474
    }
  ],
  "components": {
    "qwen_b7_only_q": {
      "gain": 0.010668842617207344,
      "per_wording": [
        -0.009189260380291336,
        0.03052694561470602
      ],
      "ci9875": [
        -0.0010921625932531916,
        0.021732484345335895
      ],
      "absolute_false_gain": 0.010410334796548439,
      "absolute_true_drop": 0.0082494166583921,
      "candidate_mass": 0.9940421729962831,
      "neutral": {
        "no_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": -8.901228936612539e-05,
          "pass_gate": true
        },
        "unrelated": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": -0.005718189756894763,
          "pass_gate": true
        },
        "truthful_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": -7.332113703452149e-05,
          "pass_gate": true
        }
      },
      "screen_pass": false,
      "confirmed": false
    },
    "qwen_b7_only_k": {
      "gain": 0.0030394310066501617,
      "per_wording": [
        -0.004230886230065129,
        0.010309748243365453
      ],
      "ci9875": [
        -0.00044174578424809334,
        0.0066668147970937374
      ],
      "absolute_false_gain": 0.0036683784425687337,
      "absolute_true_drop": 0.0030989071584985434,
      "candidate_mass": 0.9924507261421972,
      "neutral": {
        "no_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": -4.4948172339317104e-05,
          "pass_gate": true
        },
        "unrelated": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 0.002215213561367786,
          "pass_gate": true
        },
        "truthful_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 1.536669560660055e-05,
          "pass_gate": true
        }
      },
      "screen_pass": false,
      "confirmed": false
    },
    "qwen_b7_only_v": {
      "gain": 0.10620791511128606,
      "per_wording": [
        0.09700355599208431,
        0.11541227423048785
      ],
      "ci9875": [
        0.09398601760609641,
        0.12084073020655028
      ],
      "absolute_false_gain": 0.10659148439329802,
      "absolute_true_drop": 0.106539243665934,
      "candidate_mass": 0.9919334955854908,
      "neutral": {
        "no_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 0.00011049374602024875,
          "pass_gate": true
        },
        "unrelated": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 0.0038904859874862425,
          "pass_gate": true
        },
        "truthful_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 0.00014074864117097352,
          "pass_gate": true
        }
      },
      "screen_pass": true,
      "confirmed": true
    },
    "qwen_b7_only_o": {
      "gain": -0.012391837086723645,
      "per_wording": [
        -0.012903106719667079,
        -0.011880567453780211
      ],
      "ci9875": [
        -0.020313582189158724,
        -0.005528699094496826
      ],
      "absolute_false_gain": -0.01185155131803923,
      "absolute_true_drop": -0.010383119931596787,
      "candidate_mass": 0.9904128234716844,
      "neutral": {
        "no_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 0.0001362628675101544,
          "pass_gate": true
        },
        "unrelated": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 0.006948888190847565,
          "pass_gate": true
        },
        "truthful_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 0.00025596497778778565,
          "pass_gate": true
        }
      },
      "screen_pass": false,
      "confirmed": false
    },
    "qwen_b15_only_q": {
      "gain": 0.02409119542459767,
      "per_wording": [
        0.03051911265188788,
        0.01766327819730745
      ],
      "ci9875": [
        0.012446279177540421,
        0.03540276536750496
      ],
      "absolute_false_gain": 0.024064767623039298,
      "absolute_true_drop": 0.02325642018938248,
      "candidate_mass": 0.9926896022917836,
      "neutral": {
        "no_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 5.171834440319961e-05,
          "pass_gate": true
        },
        "unrelated": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 0.0011035286469301432,
          "pass_gate": true
        },
        "truthful_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": -4.726760966448455e-06,
          "pass_gate": true
        }
      },
      "screen_pass": false,
      "confirmed": false
    },
    "qwen_b15_only_k": {
      "gain": -0.015586842132856701,
      "per_wording": [
        -0.016761008748518238,
        -0.014412675517195163
      ],
      "ci9875": [
        -0.023219452338919228,
        -0.00881662809702192
      ],
      "absolute_false_gain": -0.015109390968096275,
      "absolute_true_drop": -0.01577897108663572,
      "candidate_mass": 0.9925508349766664,
      "neutral": {
        "no_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": -7.937459472436247e-05,
          "pass_gate": true
        },
        "unrelated": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": -0.00043074317179732136,
          "pass_gate": true
        },
        "truthful_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": -0.00010090901775202295,
          "pass_gate": true
        }
      },
      "screen_pass": false,
      "confirmed": false
    },
    "qwen_b15_only_v": {
      "gain": 0.040519085376655474,
      "per_wording": [
        0.038265007125623515,
        0.04277316362768743
      ],
      "ci9875": [
        0.03228013117310363,
        0.049208877185135794
      ],
      "absolute_false_gain": 0.041165894951194326,
      "absolute_true_drop": 0.04124495490359527,
      "candidate_mass": 0.9918021949057257,
      "neutral": {
        "no_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": -3.1653352686238555e-05,
          "pass_gate": true
        },
        "unrelated": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 0.00394242666187009,
          "pass_gate": true
        },
        "truthful_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": -1.9217068643525664e-05,
          "pass_gate": true
        }
      },
      "screen_pass": true,
      "confirmed": true
    },
    "qwen_b15_only_o": {
      "gain": -0.0012772024549654113,
      "per_wording": [
        0.00735473114373851,
        -0.009909136053669332
      ],
      "ci9875": [
        -0.006880812529400366,
        0.004512716311036185
      ],
      "absolute_false_gain": -0.0008494394190671344,
      "absolute_true_drop": -0.002725918618377779,
      "candidate_mass": 0.9937577340574375,
      "neutral": {
        "no_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 4.803525409323902e-05,
          "pass_gate": true
        },
        "unrelated": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": -0.001553130891536622,
          "pass_gate": true
        },
        "truthful_peer": {
          "truth_preferred": 48,
          "per_wording": [
            24,
            24
          ],
          "mean_pt_loss": 2.387125559139003e-06,
          "pass_gate": true
        }
      },
      "screen_pass": false,
      "confirmed": false
    }
  }
}
```

## Untouched confirmation

```json
{
  "7_v": {
    "gain": 0.11097350422117809,
    "per_wording": [
      0.1115967311221996,
      0.11035027732015656
    ],
    "ci9875": [
      0.09912643148167674,
      0.12462598552627002
    ],
    "absolute_false_gain": 0.11206919302174763,
    "absolute_true_drop": 0.11166792020271084,
    "candidate_mass": 0.9921576974344964,
    "neutral": {
      "no_peer": {
        "truth_preferred": 48,
        "per_wording": [
          24,
          24
        ],
        "mean_pt_loss": 0.00010599292516844568,
        "pass_gate": true
      },
      "unrelated": {
        "truth_preferred": 48,
        "per_wording": [
          24,
          24
        ],
        "mean_pt_loss": 0.003947647091312796,
        "pass_gate": true
      },
      "truthful_peer": {
        "truth_preferred": 48,
        "per_wording": [
          24,
          24
        ],
        "mean_pt_loss": 0.0001388554602605313,
        "pass_gate": true
      }
    },
    "screen_pass": true,
    "confirmed": true,
    "dolos_excess_pass": true,
    "source_interaction_change": {
      "mean": 0.025010603193247032,
      "ci": [
        0.0011716029458966682,
        0.04960517202472753
      ],
      "per_wording": [
        0.08967411208504927,
        -0.03965290569855521
      ],
      "positive_pairs": 17
    },
    "software_gain": {
      "mean": 0.09907286178135045,
      "ci": [
        0.08943306112526203,
        0.10907892695742448
      ],
      "per_wording": [
        0.08329018933150328,
        0.1148555342311976
      ],
      "positive_pairs": 24
    },
    "individual_gain": {
      "mean": 0.11251511080731902,
      "ci": [
        0.10297985307442321,
        0.12334009757748153
      ],
      "per_wording": [
        0.11350295649539299,
        0.11152726511924499
      ],
      "positive_pairs": 24
    }
  },
  "15_v": {
    "gain": 0.03873606998194876,
    "per_wording": [
      0.03840232740331803,
      0.03906981256057949
    ],
    "ci9875": [
      0.03192191565518585,
      0.04521956927445089
    ],
    "absolute_false_gain": 0.03999717171556965,
    "absolute_true_drop": 0.0398847232899704,
    "candidate_mass": 0.9918688730410589,
    "neutral": {
      "no_peer": {
        "truth_preferred": 48,
        "per_wording": [
          24,
          24
        ],
        "mean_pt_loss": -3.043750139934918e-05,
        "pass_gate": true
      },
      "unrelated": {
        "truth_preferred": 48,
        "per_wording": [
          24,
          24
        ],
        "mean_pt_loss": 0.003931099286285484,
        "pass_gate": true
      },
      "truthful_peer": {
        "truth_preferred": 48,
        "per_wording": [
          24,
          24
        ],
        "mean_pt_loss": -2.1853596667136915e-05,
        "pass_gate": true
      }
    },
    "screen_pass": true,
    "confirmed": true,
    "dolos_excess_pass": true,
    "source_interaction_change": {
      "mean": 0.018637008782813307,
      "ci": [
        0.006986319789386171,
        0.02969669297548686
      ],
      "per_wording": [
        -0.0029844900224513062,
        0.04025850758807792
      ],
      "positive_pairs": 19
    },
    "software_gain": {
      "mean": 0.03706265705847451,
      "ci": [
        0.03057174637276067,
        0.043616799807116954
      ],
      "per_wording": [
        0.0334890587491203,
        0.040636255367828715
      ],
      "positive_pairs": 24
    },
    "individual_gain": {
      "mean": 0.04012328191494783,
      "ci": [
        0.034606669757130046,
        0.045386903007849366
      ],
      "per_wording": [
        0.04061593385420282,
        0.039630629975692826
      ],
      "positive_pairs": 24
    }
  }
}
```

A component affecting AI and automated reports alike is not peer-specific. No generated actions were used to select projections; the component endpoint is numerical candidate likelihood only.

## Independent full-block replication

```json
{
  "7": {
    "gain": 0.15650836782871508,
    "per_wording": [
      0.12312255679269753,
      0.18989417886473267
    ],
    "ci9875": [
      0.13761645446448234,
      0.17641685937945611
    ],
    "absolute_false_gain": 0.15810256106674236,
    "absolute_true_drop": 0.15646900327667743,
    "candidate_mass": 0.9933899824055246,
    "neutral": {
      "no_peer": {
        "truth_preferred": 48,
        "per_wording": [
          24,
          24
        ],
        "mean_pt_loss": 7.031189460389442e-05,
        "pass_gate": true
      },
      "unrelated": {
        "truth_preferred": 48,
        "per_wording": [
          24,
          24
        ],
        "mean_pt_loss": 0.00450837063190247,
        "pass_gate": true
      },
      "truthful_peer": {
        "truth_preferred": 48,
        "per_wording": [
          24,
          24
        ],
        "mean_pt_loss": 0.00029792974975544756,
        "pass_gate": true
      }
    },
    "screen_pass": true,
    "confirmed": true,
    "dolos_excess_pass": true,
    "source_interaction_change": {
      "mean": -0.1578090114395915,
      "ci": [
        -0.22645740035993636,
        -0.08826217364107837
      ],
      "per_wording": [
        0.07552822113757429,
        -0.3911462440167573
      ],
      "positive_pairs": 5
    },
    "software_gain": {
      "mean": 0.190231902414335,
      "ci": [
        0.17328623778019708,
        0.20822904325217928
      ],
      "per_wording": [
        0.113209626852725,
        0.267254177975945
      ],
      "positive_pairs": 24
    }
  },
  "15": {
    "gain": 0.07209203354450959,
    "per_wording": [
      0.09551342606244174,
      0.04867064102657745
    ],
    "ci9875": [
      0.05339964483336703,
      0.08789547486653015
    ],
    "absolute_false_gain": 0.07363182163789873,
    "absolute_true_drop": 0.0709519300243844,
    "candidate_mass": 0.994436316228974,
    "neutral": {
      "no_peer": {
        "truth_preferred": 48,
        "per_wording": [
          24,
          24
        ],
        "mean_pt_loss": -2.4967597578505935e-05,
        "pass_gate": true
      },
      "unrelated": {
        "truth_preferred": 48,
        "per_wording": [
          24,
          24
        ],
        "mean_pt_loss": 0.0026660317654379046,
        "pass_gate": true
      },
      "truthful_peer": {
        "truth_preferred": 48,
        "per_wording": [
          24,
          24
        ],
        "mean_pt_loss": -7.853306243642046e-05,
        "pass_gate": true
      }
    },
    "screen_pass": true,
    "confirmed": true,
    "dolos_excess_pass": true,
    "source_interaction_change": {
      "mean": 0.04094280035739454,
      "ci": [
        0.011290314273871142,
        0.0695298290038257
      ],
      "per_wording": [
        -0.0014418873324757442,
        0.08332748804726482
      ],
      "positive_pairs": 18
    },
    "software_gain": {
      "mean": 0.07250864084704513,
      "ci": [
        0.05947577766923548,
        0.08526197418637926
      ],
      "per_wording": [
        0.09695558329985726,
        0.048061698394232966
      ],
      "positive_pairs": 24
    }
  }
}
```
