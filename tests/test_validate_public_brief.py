from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_public_brief import PublicBriefError, validate_brief  # noqa: E402


def example() -> dict:
    return json.loads((ROOT / "examples" / "public-brief.example.json").read_text(encoding="utf-8"))


class PublicBriefTreeTests(unittest.TestCase):
    def test_valid_partition_tree(self) -> None:
        validate_brief(example())

    def test_partition_weights_must_sum_to_one(self) -> None:
        brief = example()
        brief["actions"][0]["probability_tree"]["root"]["branches"][1]["weight"] = 0.3
        with self.assertRaisesRegex(PublicBriefError, "weights must sum to 1"):
            validate_brief(brief)

    def test_unknown_evidence_reference_is_rejected(self) -> None:
        brief = example()
        branch = brief["actions"][0]["probability_tree"]["root"]["branches"][0]
        branch["evidence_refs"] = ["missing-evidence"]
        with self.assertRaisesRegex(PublicBriefError, "unknown evidence"):
            validate_brief(brief)

    def test_unreferenced_evidence_is_rejected(self) -> None:
        brief = example()
        extra = copy.deepcopy(brief["actions"][0]["evidence"][0])
        extra["id"] = "unused-evidence"
        brief["actions"][0]["evidence"].append(extra)
        with self.assertRaisesRegex(PublicBriefError, "does not reference evidence"):
            validate_brief(brief)

    def test_non_string_evidence_reference_has_protocol_error(self) -> None:
        brief = example()
        branch = brief["actions"][0]["probability_tree"]["root"]["branches"][0]
        branch["evidence_refs"] = [{"not": "hashable"}]
        with self.assertRaisesRegex(PublicBriefError, "must be a non-empty string"):
            validate_brief(brief)

    def test_root_probability_must_equal_fair_price(self) -> None:
        brief = example()
        brief["actions"][0]["fair_price"] = 0.68
        brief["actions"][0]["price_gap"] = 0.16
        with self.assertRaisesRegex(PublicBriefError, "must equal fair_price"):
            validate_brief(brief)

    def test_bayes_posterior_is_recomputed(self) -> None:
        brief = example()
        action = brief["actions"][0]
        action["fair_price"] = 0.5
        action["price_gap"] = -0.02
        action["evidence"] = [action["evidence"][0]]
        action["probability_tree"] = {
            "root": {
                "id": "root-update",
                "type": "bayes_update",
                "label": "证据更新后的目标概率",
                "description": "从先验开始应用一条证据。",
                "probability": 0.5,
                "evidence_refs": [],
                "prior": {
                    "id": "prior",
                    "type": "estimate",
                    "label": "先验",
                    "description": "未加入新证据前的概率。",
                    "probability": 0.4,
                    "evidence_refs": [],
                },
                "updates": [
                    {
                        "id": "update-one",
                        "label": "应用政策证据",
                        "likelihood_if_true": 0.75,
                        "likelihood_if_false": 0.5,
                        "posterior_probability": 0.5,
                        "evidence_refs": ["evidence-policy"],
                    }
                ],
            }
        }
        validate_brief(brief)
        action["probability_tree"]["root"]["updates"][0]["posterior_probability"] = 0.51
        with self.assertRaisesRegex(PublicBriefError, "does not match Bayes calculation"):
            validate_brief(brief)

    def test_duplicate_tree_id_is_rejected(self) -> None:
        brief = example()
        branches = brief["actions"][0]["probability_tree"]["root"]["branches"]
        branches[1]["child"]["id"] = branches[0]["child"]["id"]
        with self.assertRaisesRegex(PublicBriefError, "duplicates ID"):
            validate_brief(brief)


if __name__ == "__main__":
    unittest.main()
