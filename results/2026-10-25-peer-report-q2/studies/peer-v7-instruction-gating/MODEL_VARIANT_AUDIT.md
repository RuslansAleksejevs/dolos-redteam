# Four-variant audit

Archived engineering controls passed before new evidence.

```json
{
  "engineering": {
    "dolos": {
      "passed": true,
      "sham_error": 0.0,
      "non_target_hash_before": "7feb0292febe9f5156014cdf822a2b3f98e07eeabe8cee628cf1558caf817545",
      "non_target_hash_after": "7feb0292febe9f5156014cdf822a2b3f98e07eeabe8cee628cf1558caf817545",
      "original_v_hashes": {
        "weight": "4e96ef3d0a4f4f3d7bcbea0b2c0be22dcc956bb4f8ed47ca0c5add6252d96a0c",
        "bias": "8f3f5a735bcf53d9c1c1de26105b7578108af08b942506d2fabe85d59e34fb62"
      },
      "donor_v_hashes": {
        "weight": "fd79c0a0421974ceb35831b8d219748b39d22c79a08063df07480f9e051fb45e",
        "bias": "43ad08c17329a1af0439e2762dcf716611399699b1adcaed9a9393d050bc31f4"
      },
      "per_wording_share_effect": {
        "original": 0.05338214349226367,
        "fresh": 0.07265987024056991
      },
      "revisions": {
        "dolos": [
          "Poseidon-Research/Dolos-1.5B",
          "63e7031a0535a49f86e08af4e7bdc45cfa22fe6d"
        ],
        "qwen": [
          "Qwen/Qwen2.5-1.5B-Instruct",
          "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
        ]
      }
    },
    "qwen": {
      "passed": true,
      "sham_error": 0.0,
      "non_target_hash_before": "f2003370e7ee0e290f84e6fcc9c3af9713c5ef36a0445d108cc59d9d49ee347e",
      "non_target_hash_after": "f2003370e7ee0e290f84e6fcc9c3af9713c5ef36a0445d108cc59d9d49ee347e",
      "original_v_hashes": {
        "weight": "fd79c0a0421974ceb35831b8d219748b39d22c79a08063df07480f9e051fb45e",
        "bias": "43ad08c17329a1af0439e2762dcf716611399699b1adcaed9a9393d050bc31f4"
      },
      "donor_v_hashes": {
        "weight": "4e96ef3d0a4f4f3d7bcbea0b2c0be22dcc956bb4f8ed47ca0c5add6252d96a0c",
        "bias": "8f3f5a735bcf53d9c1c1de26105b7578108af08b942506d2fabe85d59e34fb62"
      },
      "per_wording_share_effect": {
        "original": 0.10577848331677686,
        "fresh": 0.11140172719808986
      },
      "revisions": {
        "dolos": [
          "Poseidon-Research/Dolos-1.5B",
          "63e7031a0535a49f86e08af4e7bdc45cfa22fe6d"
        ],
        "qwen": [
          "Qwen/Qwen2.5-1.5B-Instruct",
          "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
        ]
      }
    }
  },
  "runtime": {
    "dolos": {
      "complete": true,
      "device": "NVIDIA RTX A5000",
      "dtype": "fp32",
      "torch": "2.8.0+cu128",
      "transformers": "5.7.0",
      "revisions": {
        "dolos": [
          "Poseidon-Research/Dolos-1.5B",
          "63e7031a0535a49f86e08af4e7bdc45cfa22fe6d"
        ],
        "qwen": [
          "Qwen/Qwen2.5-1.5B-Instruct",
          "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
        ]
      },
      "cache_parity_error": 4.863739013671875e-05,
      "hook_parity_error": 0.0,
      "non_target_before": "7feb0292febe9f5156014cdf822a2b3f98e07eeabe8cee628cf1558caf817545",
      "non_target_after": "7feb0292febe9f5156014cdf822a2b3f98e07eeabe8cee628cf1558caf817545",
      "original_v_hashes": {
        "weight": "4e96ef3d0a4f4f3d7bcbea0b2c0be22dcc956bb4f8ed47ca0c5add6252d96a0c",
        "bias": "8f3f5a735bcf53d9c1c1de26105b7578108af08b942506d2fabe85d59e34fb62"
      },
      "donor_v_hashes": {
        "weight": "fd79c0a0421974ceb35831b8d219748b39d22c79a08063df07480f9e051fb45e",
        "bias": "43ad08c17329a1af0439e2762dcf716611399699b1adcaed9a9393d050bc31f4"
      },
      "seconds": 475.12194442749023,
      "peak_vram": 7303686144
    },
    "qwen": {
      "complete": true,
      "device": "NVIDIA RTX A5000",
      "dtype": "fp32",
      "torch": "2.8.0+cu128",
      "transformers": "5.7.0",
      "revisions": {
        "dolos": [
          "Poseidon-Research/Dolos-1.5B",
          "63e7031a0535a49f86e08af4e7bdc45cfa22fe6d"
        ],
        "qwen": [
          "Qwen/Qwen2.5-1.5B-Instruct",
          "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
        ]
      },
      "cache_parity_error": 7.033348083496094e-05,
      "hook_parity_error": 0,
      "non_target_before": "f2003370e7ee0e290f84e6fcc9c3af9713c5ef36a0445d108cc59d9d49ee347e",
      "non_target_after": "f2003370e7ee0e290f84e6fcc9c3af9713c5ef36a0445d108cc59d9d49ee347e",
      "original_v_hashes": {
        "weight": "fd79c0a0421974ceb35831b8d219748b39d22c79a08063df07480f9e051fb45e",
        "bias": "43ad08c17329a1af0439e2762dcf716611399699b1adcaed9a9393d050bc31f4"
      },
      "donor_v_hashes": {
        "weight": "4e96ef3d0a4f4f3d7bcbea0b2c0be22dcc956bb4f8ed47ca0c5add6252d96a0c",
        "bias": "8f3f5a735bcf53d9c1c1de26105b7578108af08b942506d2fabe85d59e34fb62"
      },
      "seconds": 552.2971830368042,
      "peak_vram": 7303686144
    }
  },
  "local_reconstruction": {
    "passed": true,
    "sdpa_eager_logp_error": 5.9604644775390625e-06,
    "n": 24,
    "checks": [
      {
        "id": 8000,
        "wording": "original",
        "condition": "O|peer_ai",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.671230494248448e-06,
        "reconstruction_max_abs": 3.9637088775634766e-06,
        "virtual_actual_logp_error": 1.049041748046875e-05,
        "reinstatement_logp_error": 1.2158416211605072e-05,
        "prediction_delta_norms": [
          [
            0.9536355137825012,
            0.8951032161712646,
            0.9101009368896484
          ],
          [
            0.9536355137825012,
            0.8951032161712646,
            0.888314962387085
          ]
        ]
      },
      {
        "id": 8000,
        "wording": "original",
        "condition": "O|software_report",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.6820548454415984e-06,
        "reconstruction_max_abs": 4.0531158447265625e-06,
        "virtual_actual_logp_error": 3.4533441066741943e-06,
        "reinstatement_logp_error": 3.4533441066741943e-06,
        "prediction_delta_norms": [
          [
            0.9505330324172974,
            0.8958319425582886,
            0.9099225401878357
          ],
          [
            0.9505330324172974,
            0.8958319425582886,
            0.8895668387413025
          ]
        ]
      },
      {
        "id": 8000,
        "wording": "original",
        "condition": "E|peer_ai",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.668483820249094e-06,
        "reconstruction_max_abs": 4.500150680541992e-06,
        "virtual_actual_logp_error": 5.494803190231323e-06,
        "reinstatement_logp_error": 3.814697265625e-06,
        "prediction_delta_norms": [
          [
            0.9560988545417786,
            0.8971492052078247,
            0.9078753590583801
          ],
          [
            0.9560988545417786,
            0.8971492052078247,
            0.8873133659362793
          ]
        ]
      },
      {
        "id": 8000,
        "wording": "original",
        "condition": "E|software_report",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.661160568910418e-06,
        "reconstruction_max_abs": 4.500150680541992e-06,
        "virtual_actual_logp_error": 3.4533441066741943e-06,
        "reinstatement_logp_error": 5.122274160385132e-06,
        "prediction_delta_norms": [
          [
            0.9527594447135925,
            0.8954445719718933,
            0.9080088138580322
          ],
          [
            0.9527594447135925,
            0.8954445719718933,
            0.8894152641296387
          ]
        ]
      },
      {
        "id": 8000,
        "wording": "original",
        "condition": "P|peer_ai",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.683281299046939e-06,
        "reconstruction_max_abs": 4.4405460357666016e-06,
        "virtual_actual_logp_error": 6.556045264005661e-06,
        "reinstatement_logp_error": 5.125999450683594e-06,
        "prediction_delta_norms": [
          [
            0.953085720539093,
            0.8970070481300354,
            0.9110358953475952
          ],
          [
            0.953085720539093,
            0.8970070481300354,
            0.8918257355690002
          ]
        ]
      },
      {
        "id": 8000,
        "wording": "original",
        "condition": "P|software_report",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.671725259366212e-06,
        "reconstruction_max_abs": 4.4405460357666016e-06,
        "virtual_actual_logp_error": 4.76837158203125e-06,
        "reinstatement_logp_error": 1.6689300537109375e-06,
        "prediction_delta_norms": [
          [
            0.9494723677635193,
            0.8954322934150696,
            0.9113362431526184
          ],
          [
            0.9494723677635193,
            0.8954322934150696,
            0.8934506177902222
          ]
        ]
      },
      {
        "id": 8000,
        "wording": "fresh",
        "condition": "O|peer_ai",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.693841896776576e-06,
        "reconstruction_max_abs": 5.21540641784668e-06,
        "virtual_actual_logp_error": 2.7418136596679688e-06,
        "reinstatement_logp_error": 7.631257176399231e-06,
        "prediction_delta_norms": [
          [
            0.9569113254547119,
            0.8950240015983582,
            0.9129892587661743
          ],
          [
            0.9569113254547119,
            0.8950240015983582,
            0.8921939730644226
          ]
        ]
      },
      {
        "id": 8000,
        "wording": "fresh",
        "condition": "O|software_report",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.693207069474738e-06,
        "reconstruction_max_abs": 5.21540641784668e-06,
        "virtual_actual_logp_error": 5.1264651119709015e-06,
        "reinstatement_logp_error": 7.2713010013103485e-06,
        "prediction_delta_norms": [
          [
            0.9521464109420776,
            0.8939148783683777,
            0.9134431481361389
          ],
          [
            0.9521464109420776,
            0.8939148783683777,
            0.8905878067016602
          ]
        ]
      },
      {
        "id": 8000,
        "wording": "fresh",
        "condition": "E|peer_ai",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.657799531240016e-06,
        "reconstruction_max_abs": 5.260109901428223e-06,
        "virtual_actual_logp_error": 1.3329088687896729e-05,
        "reinstatement_logp_error": 1.1175870895385742e-07,
        "prediction_delta_norms": [
          [
            0.9581641554832458,
            0.8946941494941711,
            0.9070904850959778
          ],
          [
            0.9581641554832458,
            0.8946941494941711,
            0.8889775276184082
          ]
        ]
      },
      {
        "id": 8000,
        "wording": "fresh",
        "condition": "E|software_report",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.6880106714961585e-06,
        "reconstruction_max_abs": 4.947185516357422e-06,
        "virtual_actual_logp_error": 1.0363291949033737e-05,
        "reinstatement_logp_error": 1.6652047634124756e-06,
        "prediction_delta_norms": [
          [
            0.9547654986381531,
            0.8937946557998657,
            0.9107550978660583
          ],
          [
            0.9547654986381531,
            0.8937946557998657,
            0.8906513452529907
          ]
        ]
      },
      {
        "id": 8000,
        "wording": "fresh",
        "condition": "P|peer_ai",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.680781552859116e-06,
        "reconstruction_max_abs": 5.21540641784668e-06,
        "virtual_actual_logp_error": 5.599111318588257e-06,
        "reinstatement_logp_error": 3.6954879760742188e-06,
        "prediction_delta_norms": [
          [
            0.955042839050293,
            0.8942574262619019,
            0.9105558395385742
          ],
          [
            0.955042839050293,
            0.8942574262619019,
            0.8928015828132629
          ]
        ]
      },
      {
        "id": 8000,
        "wording": "fresh",
        "condition": "P|software_report",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.691076578135835e-06,
        "reconstruction_max_abs": 4.947185516357422e-06,
        "virtual_actual_logp_error": 2.3655593395233154e-07,
        "reinstatement_logp_error": 2.503860741853714e-06,
        "prediction_delta_norms": [
          [
            0.9516656398773193,
            0.8933692574501038,
            0.9139201641082764
          ],
          [
            0.9516656398773193,
            0.8933692574501038,
            0.8940430879592896
          ]
        ]
      },
      {
        "id": 8001,
        "wording": "original",
        "condition": "O|peer_ai",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.684234449494397e-06,
        "reconstruction_max_abs": 3.9637088775634766e-06,
        "virtual_actual_logp_error": 2.980465069413185e-06,
        "reinstatement_logp_error": 0.0,
        "prediction_delta_norms": [
          [
            0.9535918235778809,
            0.8935749530792236,
            0.92027747631073
          ],
          [
            0.9535918235778809,
            0.8935749530792236,
            0.8904504776000977
          ]
        ]
      },
      {
        "id": 8001,
        "wording": "original",
        "condition": "O|software_report",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.6688012339000124e-06,
        "reconstruction_max_abs": 3.9637088775634766e-06,
        "virtual_actual_logp_error": 3.337860107421875e-06,
        "reinstatement_logp_error": 0.0,
        "prediction_delta_norms": [
          [
            0.949968695640564,
            0.8941764831542969,
            0.9174763560295105
          ],
          [
            0.949968695640564,
            0.8941764831542969,
            0.8885093331336975
          ]
        ]
      },
      {
        "id": 8001,
        "wording": "original",
        "condition": "E|peer_ai",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.665456112386892e-06,
        "reconstruction_max_abs": 7.361173629760742e-06,
        "virtual_actual_logp_error": 5.245208740234375e-06,
        "reinstatement_logp_error": 1.7879065126180649e-06,
        "prediction_delta_norms": [
          [
            0.956003725528717,
            0.895430862903595,
            0.9136296510696411
          ],
          [
            0.956003725528717,
            0.895430862903595,
            0.8889145851135254
          ]
        ]
      },
      {
        "id": 8001,
        "wording": "original",
        "condition": "E|software_report",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.665072760370094e-06,
        "reconstruction_max_abs": 7.361173629760742e-06,
        "virtual_actual_logp_error": 3.2782554626464844e-06,
        "reinstatement_logp_error": 3.0994415283203125e-06,
        "prediction_delta_norms": [
          [
            0.9518489837646484,
            0.8927146196365356,
            0.9107375144958496
          ],
          [
            0.9518489837646484,
            0.8927146196365356,
            0.8874931931495667
          ]
        ]
      },
      {
        "id": 8001,
        "wording": "original",
        "condition": "P|peer_ai",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.670137736364268e-06,
        "reconstruction_max_abs": 7.361173629760742e-06,
        "virtual_actual_logp_error": 7.152557373046875e-06,
        "reinstatement_logp_error": 0.0,
        "prediction_delta_norms": [
          [
            0.9530740976333618,
            0.8954858183860779,
            0.918267011642456
          ],
          [
            0.9530740976333618,
            0.8954858183860779,
            0.892002284526825
          ]
        ]
      },
      {
        "id": 8001,
        "wording": "original",
        "condition": "P|software_report",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.682750154141104e-06,
        "reconstruction_max_abs": 7.361173629760742e-06,
        "virtual_actual_logp_error": 1.6689300537109375e-06,
        "reinstatement_logp_error": 3.337860107421875e-06,
        "prediction_delta_norms": [
          [
            0.9486203193664551,
            0.8927459716796875,
            0.9162430167198181
          ],
          [
            0.9486203193664551,
            0.8927459716796875,
            0.8903806805610657
          ]
        ]
      },
      {
        "id": 8001,
        "wording": "fresh",
        "condition": "O|peer_ai",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.6764109760697465e-06,
        "reconstruction_max_abs": 3.9637088775634766e-06,
        "virtual_actual_logp_error": 6.556045264005661e-06,
        "reinstatement_logp_error": 2.861255779862404e-06,
        "prediction_delta_norms": [
          [
            0.9567654728889465,
            0.8938234448432922,
            0.9224648475646973
          ],
          [
            0.9567654728889465,
            0.8938234448432922,
            0.8917137384414673
          ]
        ]
      },
      {
        "id": 8001,
        "wording": "fresh",
        "condition": "O|software_report",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.693841442029225e-06,
        "reconstruction_max_abs": 4.082918167114258e-06,
        "virtual_actual_logp_error": 1.430511474609375e-06,
        "reinstatement_logp_error": 7.987022399902344e-06,
        "prediction_delta_norms": [
          [
            0.9527276754379272,
            0.8920409083366394,
            0.9188874959945679
          ],
          [
            0.9527276754379272,
            0.8920409083366394,
            0.8906189799308777
          ]
        ]
      },
      {
        "id": 8001,
        "wording": "fresh",
        "condition": "E|peer_ai",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.658584879914997e-06,
        "reconstruction_max_abs": 4.5299530029296875e-06,
        "virtual_actual_logp_error": 1.2159347534179688e-05,
        "reinstatement_logp_error": 6.556743755936623e-06,
        "prediction_delta_norms": [
          [
            0.957980215549469,
            0.8930356502532959,
            0.9123629927635193
          ],
          [
            0.957980215549469,
            0.8930356502532959,
            0.8889408111572266
          ]
        ]
      },
      {
        "id": 8001,
        "wording": "fresh",
        "condition": "E|software_report",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.681795184704242e-06,
        "reconstruction_max_abs": 5.036592483520508e-06,
        "virtual_actual_logp_error": 2.7418136596679688e-06,
        "reinstatement_logp_error": 5.245208740234375e-06,
        "prediction_delta_norms": [
          [
            0.9552828669548035,
            0.8916676640510559,
            0.9116754531860352
          ],
          [
            0.9552828669548035,
            0.8916676640510559,
            0.8899845480918884
          ]
        ]
      },
      {
        "id": 8001,
        "wording": "fresh",
        "condition": "P|peer_ai",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.675867552985437e-06,
        "reconstruction_max_abs": 4.202127456665039e-06,
        "virtual_actual_logp_error": 3.635883331298828e-06,
        "reinstatement_logp_error": 2.1457672119140625e-06,
        "prediction_delta_norms": [
          [
            0.9549717903137207,
            0.8928453922271729,
            0.9171686172485352
          ],
          [
            0.9549717903137207,
            0.8928453922271729,
            0.8913512229919434
          ]
        ]
      },
      {
        "id": 8001,
        "wording": "fresh",
        "condition": "P|software_report",
        "upstream_max": 0.0,
        "q_max": 0.0,
        "k_max": 0.0,
        "attention_max": 0.0,
        "reconstruction_relative_l2": 6.708304681524169e-06,
        "reconstruction_max_abs": 5.036592483520508e-06,
        "virtual_actual_logp_error": 1.5139579772949219e-05,
        "reinstatement_logp_error": 1.6689300537109375e-06,
        "prediction_delta_norms": [
          [
            0.9521875977516174,
            0.891595721244812,
            0.9168571829795837
          ],
          [
            0.9521875977516174,
            0.891595721244812,
            0.8923869132995605
          ]
        ]
      }
    ]
  }
}
```
