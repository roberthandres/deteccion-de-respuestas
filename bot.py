
import time
from playwright.sync_api import sync_playwright

USER_DATA_DIR = "./whatsapp_session"
PHONE_NUMBER = "573148509549"

MESSAGE_TEXT = (
    "Soy un bot de prueba fabricado por el mejor profe. "
    "Este es un mensaje automático de prueba. ¡Gracias!"
)

INTERVAL_SECONDS = 10
CHECK_FREQUENCY = 2
MAX_REMINDERS = 3


def obtener_respuestas(page):
    """Obtiene únicamente los mensajes recibidos."""

    mensajes = page.locator('[data-testid="msg-container"]')
    respuestas = []

    for i in range(mensajes.count()):

        elemento = mensajes.nth(i)

        es_entrante = elemento.locator(
            '[data-icon="tail-in"]'
        ).count() > 0

        if not es_entrante:
            continue

        datos = elemento.evaluate("""
            (el) => {
                const contenedor = el.closest(
                    '[data-testid^="conv-msg-"]'
                );

                const texto = el.querySelector(
                    '[data-testid="selectable-text"]'
                );

                return {
                    id: contenedor
                        ? contenedor.getAttribute("data-id")
                        : null,
                    texto: texto
                        ? texto.innerText.trim()
                        : el.innerText.trim()
                };
            }
        """)

        if datos["texto"]:
            respuestas.append(datos)

    return respuestas


def enviar_mensaje(page, texto):

    cuadro = page.locator(
        'footer [contenteditable="true"][role="textbox"]'
    ).first

    cuadro.click()
    cuadro.fill(texto)
    page.keyboard.press("Enter")


def ejecutar_bot():

    with sync_playwright() as p:

        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=["--start-maximized"]
        )

        try:

            page = (
                browser.pages[0]
                if browser.pages
                else browser.new_page()
            )

            page.goto("https://web.whatsapp.com")

            print("\n" + "=" * 50)
            print("Espera a que cargue WhatsApp Web.")
            input("Presiona ENTER cuando estén cargados los chats.")
            print("=" * 50)

            print(f"\nAbriendo chat: {PHONE_NUMBER}")

            page.goto(
                f"https://web.whatsapp.com/send?phone={PHONE_NUMBER}"
            )

            cuadro = page.locator(
                'footer [contenteditable="true"][role="textbox"]'
            ).first

            cuadro.wait_for(
                state="visible",
                timeout=60000
            )

            time.sleep(3)

            # Guardar los mensajes recibidos que ya existían.
            respuestas_iniciales = obtener_respuestas(page)

            ids_vistos = {
                respuesta["id"]
                for respuesta in respuestas_iniciales
                if respuesta["id"]
            }

            print("\nChat cargado.")
            print("Mensajes recibidos anteriores:", len(ids_vistos))

            # Enviar el primer mensaje.
            enviar_mensaje(page, MESSAGE_TEXT)

            print("\nMensaje inicial enviado.")

            recordatorios = 0
            ultimo_envio = time.time()

            while True:

                time.sleep(CHECK_FREQUENCY)

                respuestas_actuales = obtener_respuestas(page)

                respuesta_nueva = None

                for respuesta in respuestas_actuales:

                    identificador = respuesta["id"]

                    if identificador and identificador not in ids_vistos:

                        respuesta_nueva = respuesta
                        break

                if respuesta_nueva:

                    print("\n" + "=" * 50)
                    print("¡RESPUESTA RECIBIDA!")
                    print("Mensaje:", respuesta_nueva["texto"])
                    print("=" * 50)

                    print("Se detienen los recordatorios.")
                    break

                # Registrar los mensajes entrantes que ya conocemos.
                for respuesta in respuestas_actuales:

                    if respuesta["id"]:
                        ids_vistos.add(respuesta["id"])

                # Comprobar si corresponde enviar un recordatorio.
                if time.time() - ultimo_envio >= INTERVAL_SECONDS:

                    if recordatorios >= MAX_REMINDERS:

                        print("\nMáximo de recordatorios alcanzado.")
                        break

                    enviar_mensaje(page, MESSAGE_TEXT)

                    recordatorios += 1
                    ultimo_envio = time.time()

                    print(
                        f"[{time.strftime('%H:%M:%S')}] "
                        f"Recordatorio enviado "
                        f"({recordatorios}/{MAX_REMINDERS})"
                    )

            print("\nBot finalizado.")

        except KeyboardInterrupt:

            print("\nPrograma detenido manualmente.")

        except Exception as error:

            print("\nError:", error)

        finally:

            print("Cerrando navegador...")

            try:
                browser.close()
            except Exception:
                pass

            print("Programa finalizado.")


if __name__ == "__main__":
    ejecutar_bot()
