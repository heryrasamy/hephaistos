from pprint import pprint

from SRC.francetravail_api import get_rome_job_profile


def main() -> None:
    rome_code = "M1607"

    try:
        profile = get_rome_job_profile(rome_code)

        print(f"Fiche ROME récupérée pour : {rome_code}")
        print("Type :", type(profile))
        print("Clés principales :", list(profile.keys()) if isinstance(profile, dict) else "N/A")

        pprint(profile)

    except Exception as exc:
        print("Erreur :", exc)


if __name__ == "__main__":
    main()