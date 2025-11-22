import base64
import json
import os

from googleapiclient import discovery

# Budujemy klienta API tylko raz
compute = discovery.build("compute", "v1")


def stop_vm(request):
    """HTTP handler dla Cloud Functions Gen2 (Eventarc -> Pub/Sub)."""

    try:
        envelope = request.get_json(silent=True)
        if not envelope:
            print("Brak JSON w żądaniu.")
            return ("", 204)

        # Eventarc Pub/Sub -> Cloud Functions: dane są w envelope["message"]["data"]
        message = envelope.get("message", {})
        data_b64 = message.get("data")
        if not data_b64:
            print("Brak message.data w payloadzie.")
            return ("", 204)

        pubsub_message_str = base64.b64decode(data_b64).decode("utf-8")
        incident_data = json.loads(pubsub_message_str)

        print(f"Otrzymano wiadomość: {incident_data}")

        # Payload z Alerting zwykle ma pole "incident"
        incident = incident_data.get("incident", incident_data)

        # 1. Sprawdź, czy alert jest nowy (OPEN)
        if incident.get("state") and incident.get("state").lower() != "open":
            print("Ignorowanie, alert nie jest w stanie OPEN.")
            return ("", 204)

        # 2. Dane o zasobie (VM)
        resource = incident.get("resource", {}) or {}
        labels = resource.get("labels", {}) or {}

        # resource_display_name – np. "instance-name"
        instance_name = incident.get("resource_display_name")
        zone = labels.get("zone")
        project = labels.get("project_id") or os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")

        print(f"Wyciągnięte z alertu: project={project}, zone={zone}, instance_name={instance_name}")

        if not project or not zone or not instance_name:
            print("Brak wymaganych danych do zatrzymania VM (project/zone/instance_name).")
            return ("", 204)

        # 3. Wykonaj akcję: ZATRZYMAJ MASZYNĘ
        print(f"Wysyłanie polecenia zatrzymania dla {instance_name} w {zone}...")

        request_stop = compute.instances().stop(
            project=project,
            zone=zone,
            instance=instance_name,
        )
        response = request_stop.execute()
        print(f"Polecenie wysłane. Odpowiedź API: {response}")

        return ("", 200)

    except Exception as e:
        print(f"BŁĄD KRYTYCZNY: {e}")
        return ("", 500)
