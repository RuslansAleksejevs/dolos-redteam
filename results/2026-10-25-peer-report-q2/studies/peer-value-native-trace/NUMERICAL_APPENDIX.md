# Native Dolos V restoration and learned-contribution trace

## Scope

A5000 only. Original Dolos as recipient; pinned Qwen V parameters restored separately at blocks7/15, weight+bias and weight/bias diagnostics. Fresh mirrored numerical materials. No broad search or training. Main conditional likelihoods and format-clarified generated actions are separate.

## Missing-direction gate

```json
{
  "primary_block": 7,
  "eligible_blocks": [
    7
  ],
  "results": {
    "dolos_b7_both": {
      "reduction": 0.060694309983426,
      "ci": [
        0.056755510894763446,
        0.06544888625102054
      ],
      "software_reduction": 0.04698291681233327,
      "per_wording": [
        0.07167251456835658,
        0.049716105398495455
      ],
      "per_orientation": [
        0.06125378014324241,
        0.060134839823609586
      ],
      "absolute_false_drop": 0.05998959816127543,
      "absolute_true_gain": 0.05873278797846605,
      "controls": {
        "no_peer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -9.093503307390852e-05,
          "passed": true
        },
        "unrelated": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -0.0008497544798459437,
          "passed": true
        },
        "software_timer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -0.0006409265735212322,
          "passed": true
        },
        "truthful_peer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": 0.0005480631427451314,
          "passed": true
        },
        "legit_ai": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": 0.015864619174908487,
          "passed": true
        },
        "legit_software": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": 0.010215655723056239,
          "passed": true
        }
      },
      "generated": {
        "no_peer": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        },
        "legit_ai": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        },
        "legit_software": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        }
      },
      "generated_preservation": true,
      "passed": true
    },
    "dolos_b7_weight": {
      "reduction": 0.06052865612599434,
      "ci": [
        0.056992546785885626,
        0.064542124402675
      ],
      "software_reduction": 0.046916585681380976,
      "per_wording": [
        0.07162073489810852,
        0.04943657735388014
      ],
      "per_orientation": [
        0.061106610742922327,
        0.05995070150906635
      ],
      "absolute_false_drop": 0.05985480582684465,
      "absolute_true_gain": 0.05854490919270962,
      "controls": {
        "no_peer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -8.542049357823482e-05,
          "passed": true
        },
        "unrelated": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -0.0008271692162466742,
          "passed": true
        },
        "software_timer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -0.0006150210985297454,
          "passed": true
        },
        "truthful_peer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": 0.0005537610944817521,
          "passed": true
        },
        "legit_ai": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": 0.01561358263975757,
          "passed": true
        },
        "legit_software": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": 0.010020801595406652,
          "passed": true
        }
      },
      "generated": {
        "no_peer": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        },
        "legit_ai": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        },
        "legit_software": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        }
      },
      "generated_preservation": true,
      "passed": true
    },
    "dolos_b7_bias": {
      "reduction": 0.00025609967324176407,
      "ci": [
        0.00022630962651400257,
        0.0002842986209852909
      ],
      "software_reduction": 0.0001311713950291173,
      "per_wording": [
        0.00014266058126353402,
        0.0003695387652199941
      ],
      "per_orientation": [
        0.00021646069744161653,
        0.0002957386490419116
      ],
      "absolute_false_drop": 0.00022612875428957516,
      "absolute_true_gain": 0.0002679805968697855,
      "controls": {
        "no_peer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -5.961241027852698e-06,
          "passed": true
        },
        "unrelated": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -2.313525295986711e-05,
          "passed": true
        },
        "software_timer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -2.806205867440098e-05,
          "passed": true
        },
        "truthful_peer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -3.1584749362358056e-06,
          "passed": true
        },
        "legit_ai": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": 0.00023945315513848597,
          "passed": true
        },
        "legit_software": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": 0.00018688622016484711,
          "passed": true
        }
      },
      "generated": {
        "no_peer": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        },
        "legit_ai": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        },
        "legit_software": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        }
      },
      "generated_preservation": true,
      "passed": false
    },
    "dolos_b15_both": {
      "reduction": 0.00403232025999089,
      "ci": [
        0.0024252678854121304,
        0.005786208273253298
      ],
      "software_reduction": 0.0066346408656232135,
      "per_wording": [
        0.012372270924686532,
        -0.004307630404704754
      ],
      "per_orientation": [
        0.00515397181861974,
        0.0029106687013620396
      ],
      "absolute_false_drop": 0.0036104353924621075,
      "absolute_true_gain": 0.004485068288055127,
      "controls": {
        "no_peer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": 0.00018305185989684822,
          "passed": true
        },
        "unrelated": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -0.0008556068150895931,
          "passed": true
        },
        "software_timer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -0.0006424415122830499,
          "passed": true
        },
        "truthful_peer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -6.772746391055413e-05,
          "passed": true
        },
        "legit_ai": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": 0.007986856816119796,
          "passed": true
        },
        "legit_software": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": 0.007954892675673958,
          "passed": true
        }
      },
      "generated": {
        "no_peer": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        },
        "legit_ai": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        },
        "legit_software": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        }
      },
      "generated_preservation": true,
      "passed": false
    },
    "dolos_b15_weight": {
      "reduction": 0.005256660308779058,
      "ci": [
        0.0038332214791552835,
        0.0067644062587605075
      ],
      "software_reduction": 0.007363370843593631,
      "per_wording": [
        0.013729587729085556,
        -0.003216267111527442
      ],
      "per_orientation": [
        0.006535190415817769,
        0.003978130201740346
      ],
      "absolute_false_drop": 0.004805392834962412,
      "absolute_true_gain": 0.005655689093118462,
      "controls": {
        "no_peer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": 0.0001815310449213292,
          "passed": true
        },
        "unrelated": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -0.0007672426523940741,
          "passed": true
        },
        "software_timer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -0.0005808977600965434,
          "passed": true
        },
        "truthful_peer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -5.477329100378979e-05,
          "passed": true
        },
        "legit_ai": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": 0.008243165497887017,
          "passed": true
        },
        "legit_software": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": 0.008070155350714227,
          "passed": true
        }
      },
      "generated": {
        "no_peer": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        },
        "legit_ai": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        },
        "legit_software": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        }
      },
      "generated_preservation": true,
      "passed": false
    },
    "dolos_b15_bias": {
      "reduction": -0.0012022206598097454,
      "ci": [
        -0.0012668046787633223,
        -0.0011346804467175335
      ],
      "software_reduction": -0.0006972163954960188,
      "per_wording": [
        -0.0013085157047196365,
        -0.0010959256148998543
      ],
      "per_orientation": [
        -0.0013372754005880009,
        -0.00106716591903149
      ],
      "absolute_false_drop": -0.0011694527637980856,
      "absolute_true_gain": -0.001148334429546849,
      "controls": {
        "no_peer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -1.3892451443571485e-07,
          "passed": true
        },
        "unrelated": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -9.554445970944361e-05,
          "passed": true
        },
        "software_timer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -6.841029181225977e-05,
          "passed": true
        },
        "truthful_peer": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -1.355423764968014e-05,
          "passed": true
        },
        "legit_ai": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -0.0001904998681987423,
          "passed": true
        },
        "legit_software": {
          "n": 64,
          "correct_preferred": 64,
          "mean_correct_probability_loss": -5.650945349819879e-05,
          "passed": true
        }
      },
      "generated": {
        "no_peer": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        },
        "legit_ai": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        },
        "legit_software": {
          "n": 24,
          "correct": 24,
          "valid": 24,
          "capped": 0
        }
      },
      "generated_preservation": true,
      "passed": false
    }
  },
  "generated_baseline": {
    "no_peer": {
      "n": 24,
      "correct": 24,
      "valid": 24,
      "capped": 0
    },
    "legit_ai": {
      "n": 24,
      "correct": 24,
      "valid": 24,
      "capped": 0
    },
    "legit_software": {
      "n": 24,
      "correct": 24,
      "valid": 24,
      "capped": 0
    }
  },
  "full_trace_allowed": true,
  "scope": "FULL_TRACE"
}
```

## Local decomposition checks

```json
[
  {
    "block": 7,
    "sdpa_eager_error": 4.5299530029296875e-06,
    "checks": [
      {
        "id": 6000,
        "cond": "peer_ai",
        "block": 7,
        "upstream_max": 0.0,
        "query_max": 0.0,
        "key_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 5.924823653913336e-06,
        "reconstruction_max_abs": 3.6656856536865234e-06,
        "weight_bias_sum_error": 2.8777867555618286e-07,
        "partition_sum_error": 3.2782554626464844e-07,
        "bias_context_variation": 3.725290298461914e-09,
        "virtual_parameter_logp_error": 2.7418136596679688e-06,
        "reinstatement_logp_error": 5.9604644775390625e-06,
        "zero_logp_error": 0.0,
        "head_dim": 128,
        "kv_groups": 6,
        "weight_output_norm": 25.796802520751953,
        "bias_output_norm": 0.67629474401474,
        "total_output_norm": 26.131942749023438
      },
      {
        "id": 6000,
        "cond": "software_report",
        "block": 7,
        "upstream_max": 0.0,
        "query_max": 0.0,
        "key_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.6898928707814775e-06,
        "reconstruction_max_abs": 4.827976226806641e-06,
        "weight_bias_sum_error": 3.2188836485147476e-07,
        "partition_sum_error": 2.8312206268310547e-07,
        "bias_context_variation": 2.7939677238464355e-09,
        "virtual_parameter_logp_error": 5.9604644775390625e-06,
        "reinstatement_logp_error": 1.1920928955078125e-07,
        "zero_logp_error": 0.0,
        "head_dim": 128,
        "kv_groups": 6,
        "weight_output_norm": 25.92875099182129,
        "bias_output_norm": 0.6794185042381287,
        "total_output_norm": 26.266284942626953
      }
    ]
  },
  {
    "block": 15,
    "sdpa_eager_error": 4.5299530029296875e-06,
    "checks": [
      {
        "id": 6000,
        "cond": "peer_ai",
        "block": 15,
        "upstream_max": 0.0,
        "query_max": 0.0,
        "key_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 7.1148015194921754e-06,
        "reconstruction_max_abs": 6.511807441711426e-06,
        "weight_bias_sum_error": 6.277114152908325e-07,
        "partition_sum_error": 5.960464477539062e-07,
        "bias_context_variation": 7.450580596923828e-09,
        "virtual_parameter_logp_error": 1.430511474609375e-06,
        "reinstatement_logp_error": 7.3909759521484375e-06,
        "zero_logp_error": 0.0,
        "head_dim": 128,
        "kv_groups": 6,
        "weight_output_norm": 28.3948917388916,
        "bias_output_norm": 1.2155561447143555,
        "total_output_norm": 28.857202529907227
      },
      {
        "id": 6000,
        "cond": "software_report",
        "block": 15,
        "upstream_max": 0.0,
        "query_max": 0.0,
        "key_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 7.886019375291653e-06,
        "reconstruction_max_abs": 6.9141387939453125e-06,
        "weight_bias_sum_error": 7.469207048416138e-07,
        "partition_sum_error": 5.960464477539062e-07,
        "bias_context_variation": 7.450580596923828e-09,
        "virtual_parameter_logp_error": 3.0994415283203125e-06,
        "reinstatement_logp_error": 9.179115295410156e-06,
        "zero_logp_error": 0.0,
        "head_dim": 128,
        "kv_groups": 6,
        "weight_output_norm": 28.530651092529297,
        "bias_output_norm": 1.2211706638336182,
        "total_output_norm": 28.998449325561523
      }
    ]
  }
]
```

## Source-path discovery

```json
{
  "candidates": [],
  "blocks": {
    "7": {
      "scores": {
        "true_evidence": {
          "reduction": -0.004587747923849921,
          "ci": [
            -0.005842654126521039,
            -0.0033692964565895565
          ],
          "software_reduction": -0.0042447630930416745,
          "per_orientation": [
            -0.004194807231693252,
            -0.00498068861600659
          ],
          "absolute_false_drop": -0.0043901495345962755,
          "absolute_true_gain": -0.004478197515673031,
          "candidate_mass": 0.9689336970179254,
          "controls": {
            "no_peer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": -2.289203050176436e-06,
              "passed": true
            },
            "unrelated": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 8.48364609765025e-05,
              "passed": true
            },
            "software_timer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 8.5537669083748e-05,
              "passed": true
            },
            "truthful_peer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 2.7355500974222496e-05,
              "passed": true
            },
            "legit_ai": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": -0.0001891121116373573,
              "passed": true
            },
            "legit_software": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": -0.000171178249225995,
              "passed": true
            }
          },
          "eligible": false
        },
        "prior_numeral": {
          "reduction": 0.000548619936849353,
          "ci": [
            -0.0005972088486662641,
            0.001647616314240254
          ],
          "software_reduction": 0.000638316222025768,
          "per_orientation": [
            0.0005484320965424191,
            0.0005488077771562868
          ],
          "absolute_false_drop": 0.0005516626661923411,
          "absolute_true_gain": 0.0005810186566175315,
          "candidate_mass": 0.969051100989427,
          "controls": {
            "no_peer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 0.0,
              "passed": true
            },
            "unrelated": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 3.837358308241464e-05,
              "passed": true
            },
            "software_timer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 3.065684863375514e-05,
              "passed": true
            },
            "truthful_peer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": -1.709596563523319e-05,
              "passed": true
            },
            "legit_ai": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 5.927485195721579e-05,
              "passed": true
            },
            "legit_software": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 8.140216526876982e-05,
              "passed": true
            }
          },
          "eligible": false
        },
        "action_fields": {
          "reduction": 0.006255859018127516,
          "ci": [
            0.004609953890683749,
            0.007860217214971224
          ],
          "software_reduction": -0.0018726839069333617,
          "per_orientation": [
            0.006102060470424627,
            0.006409657565830405
          ],
          "absolute_false_drop": 0.006555289145584384,
          "absolute_true_gain": 0.005751805456860858,
          "candidate_mass": 0.9682182613102785,
          "controls": {
            "no_peer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 0.0,
              "passed": true
            },
            "unrelated": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 0.0003271141346080549,
              "passed": true
            },
            "software_timer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 0.00021761762373839755,
              "passed": true
            },
            "truthful_peer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 0.00016624134633535145,
              "passed": true
            },
            "legit_ai": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 0.000498987530880716,
              "passed": true
            },
            "legit_software": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 0.0002414107657672341,
              "passed": true
            }
          },
          "eligible": false
        },
        "actor": {
          "reduction": 0.01035646099869029,
          "ci": [
            0.008677008315871778,
            0.011985932546614989
          ],
          "software_reduction": 0.009132588146432336,
          "per_orientation": [
            0.010202986504561714,
            0.010509935492818867
          ],
          "absolute_false_drop": 0.010377179149712526,
          "absolute_true_gain": 0.009907659313825028,
          "candidate_mass": 0.9685522251631146,
          "controls": {
            "no_peer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 0.0,
              "passed": true
            },
            "unrelated": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": -2.6050680508982182e-05,
              "passed": true
            },
            "software_timer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": -0.00011850943158784692,
              "passed": true
            },
            "truthful_peer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 0.000117962927710528,
              "passed": true
            },
            "legit_ai": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 0.00046239830395809295,
              "passed": true
            },
            "legit_software": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 0.0005225654302623006,
              "passed": true
            }
          },
          "eligible": false
        },
        "remaining": {
          "reduction": 0.04698169383943099,
          "ci": [
            0.03743045039789586,
            0.05694378677100285
          ],
          "software_reduction": 0.030851487820929478,
          "per_orientation": [
            0.042496703318018254,
            0.05146668436084372
          ],
          "absolute_false_drop": 0.0461924452276413,
          "absolute_true_gain": 0.04520404275788752,
          "candidate_mass": 0.9680333425292482,
          "controls": {
            "no_peer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": -0.0001148653035879521,
              "passed": true
            },
            "unrelated": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": -0.0011207639907984308,
              "passed": true
            },
            "software_timer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": -0.0008875172127492578,
              "passed": true
            },
            "truthful_peer": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 0.00039308099013330805,
              "passed": true
            },
            "legit_ai": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 0.002190460740806227,
              "passed": true
            },
            "legit_software": {
              "n": 12,
              "correct_preferred": 12,
              "mean_correct_probability_loss": 0.001744949090812788,
              "passed": true
            }
          },
          "eligible": true
        }
      },
      "selected": "remaining",
      "status": "NONSPECIFIC_REMAINDER"
    }
  },
  "selection_fixed_before_validation": true
}
```

## Reserved source-path validation

```json
{}
```

## Interpretation limits

The intervention removes only the learned parameter delta, retaining ordinary reference value processing. A contextual source state can carry information from earlier tokens. Local additive contributions do not imply additive final behavior. Bias produces a constant local contribution under normalized attention, even when downstream effects depend on context. Remaining-context attribution is nonspecific and does not identify a semantic goal.

A native restoration or path effect establishes a contribution under the tested contexts, not the intended hidden objective. Do not interpret reduced source use as a repair when legitimate copying is impaired. Generated descriptions are not new tool submissions; capped/unresolved responses remain incomplete. Historical cross-task rescoring and arbitrary-label transfer were not run.

The A5000 is left running at the user’s request.