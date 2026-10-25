"""Use the original matched evaluation with extension provenance."""
from bridge import provenance
import evaluate

if __name__ == "__main__":
    evaluate.provenance = provenance
    evaluate.main()
