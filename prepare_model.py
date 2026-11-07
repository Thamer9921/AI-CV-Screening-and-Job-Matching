"""Optional model download for first-time setup."""
import argparse
import os


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main():
    parser = argparse.ArgumentParser(
        description="Prepare the model for offline use."
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Allow downloading the public model from Hugging Face.",
    )
    args = parser.parse_args()

    if not args.download:
        print("No network request made.")
        print("To download the model, explicitly run:")
        print("python prepare_model.py --download")
        return

    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ.pop("HF_HUB_OFFLINE", None)
    os.environ.pop("TRANSFORMERS_OFFLINE", None)

    from sentence_transformers import SentenceTransformer

    print("Preparing model:", MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME, device="cpu")
    vector = model.encode(["Model setup test"])

    print("Model ready for offline use.")
    print("Test shape:", vector.shape)


if __name__ == "__main__":
    main()