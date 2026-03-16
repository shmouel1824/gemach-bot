from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from rapidfuzz import process, fuzz
from .models import Medicine, Visitor, MissedRequest
import os
import anthropic
import requests
import base64

SIMILARITY_THRESHOLD = 65

twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)
TWILIO_NUMBER = f"whatsapp:{os.getenv('TWILIO_WHATSAPP_NUMBER')}"
ADMIN_NUMBER  = f"whatsapp:{os.getenv('ADMIN_WHATSAPP')}"


def quantity_label(quantity):
    """
    Returns a colored emoji label based on quantity.
    """
    if quantity == 0:
        return "❌ אזל | Out of stock"
    elif quantity <= 2:
        return f"⚠️ כמות נמוכה | Low stock ({quantity} units)"
    else:
        return f"✅ זמין | Available ({quantity} units)"


def notify_admin(medicine_searched, requester_phone, suggestion=None):
    MissedRequest.objects.create(
        medicine_searched = medicine_searched,
        requester_phone   = requester_phone,
        suggestion_given  = suggestion
    )

    if suggestion:
        alert = (
            f"⚠️ *גמ\"ח תרופות — התראה*\n\n"
            f"מישהו חיפש: *{medicine_searched}*\n"
            f"התרופה לא נמצאה.\n"
            f"הצעה שניתנה: *{suggestion}*\n\n"
            f"📞 מספר המבקש: {requester_phone}\n\n"
            f"──\n"
            f"⚠️ *Gemach Alert*\n"
            f"Someone searched: *{medicine_searched}*\n"
            f"Not found. Suggestion given: *{suggestion}*\n"
            f"Requester: {requester_phone}"
        )
    else:
        alert = (
            f"⚠️ *גמ\"ח תרופות — התראה*\n\n"
            f"מישהו חיפש: *{medicine_searched}*\n"
            f"התרופה לא נמצאה ולא ניתנה הצעה.\n\n"
            f"📞 מספר המבקש: {requester_phone}\n\n"
            f"──\n"
            f"⚠️ *Gemach Alert*\n"
            f"Someone searched: *{medicine_searched}*\n"
            f"Not found. No suggestion given.\n"
            f"Requester: {requester_phone}"
        )

    try:
        twilio_client.messages.create(
            from_ = TWILIO_NUMBER,
            to    = ADMIN_NUMBER,
            body  = alert
        )
    except Exception as e:
        print(f"Admin notification failed: {e}")


def notify_admin_low_stock(medicine):
    """
    Alert admin when a medicine quantity reaches LOW or ZERO.
    """
    if medicine.quantity == 0:
        alert = (
            f"🚨 *גמ\"ח — אזל מהמלאי!*\n\n"
            f"התרופה *{medicine.name}*"
            + (f" ({medicine.name_hebrew})" if medicine.name_hebrew else "") +
            f" אזלה לחלוטין!\n\n"
            f"🚨 *Gemach — Out of Stock!*\n"
            f"*{medicine.name}* is now completely out of stock!"
        )
    else:
        alert = (
            f"⚠️ *גמ\"ח — מלאי נמוך!*\n\n"
            f"נותרו רק *{medicine.quantity}* יחידות של *{medicine.name}*"
            + (f" ({medicine.name_hebrew})" if medicine.name_hebrew else "") +
            f"!\n\n"
            f"⚠️ *Gemach — Low Stock!*\n"
            f"Only *{medicine.quantity}* unit(s) of *{medicine.name}* remaining!"
        )

    try:
        twilio_client.messages.create(
            from_ = TWILIO_NUMBER,
            to    = ADMIN_NUMBER,
            body  = alert
        )
    except Exception as e:
        print(f"Low stock notification failed: {e}")


def get_medicine_list():
    medicines = Medicine.objects.all().order_by('name')

    if not medicines:
        return (
            "⚠️ המאגר שלנו ריק כרגע. נסה שוב מאוחר יותר.\n"
            "⚠️ Our database is currently empty. Please try again later."
        )

    lines = ["💊 *תרופות זמינות | Available Medicines:*\n"]

    for med in medicines:
        heb = f" | {med.name_hebrew}" if med.name_hebrew else ""
        if med.quantity == 0:
            status = "❌"
        elif med.quantity <= 2:
            status = f"⚠️ ({med.quantity})"
        else:
            status = f"✅ ({med.quantity})"
        lines.append(f"  {status} {med.name}{heb}")

    lines.append(
        "\n✅ = זמין | Available\n"
        "⚠️ = כמות נמוכה | Low stock\n"
        "❌ = אזל | Out of stock\n\n"
        "📩 שלח/י שם תרופה לבדיקה.\n"
        "📩 Send a medicine name to check."
    )
    return "\n".join(lines)


def get_welcome_message():
    return (
        "🙏 *ברוכים הבאים לגמ\"ח תרופות!*\n"
        "🙏 *Welcome to our Pharmacy Gemach!*\n\n"
        "אנחנו כאן כדי לעזור לך למצוא תרופות זמינות.\n"
        "We are here to help you find available medicines.\n\n"
        "📌 *איך להשתמש | How to use:*\n"
        "  • שלח/י שם תרופה ← לבדיקת זמינות\n"
        "  • Send a medicine name ← to check availability\n"
        "  • שלח/י *LIST* או *רשימה* ← לכל התרופות\n"
        "  • Send *LIST* or *רשימה* ← for all medicines\n\n"
        "בהצלחה! 💊"
    )


def search_medicine(incoming_msg):
    exact = Medicine.objects.filter(name__iexact=incoming_msg).first()
    if exact:
        return exact, exact.name, False, 100

    exact_heb = Medicine.objects.filter(
        name_hebrew__iexact=incoming_msg
    ).first()
    if exact_heb:
        return exact_heb, exact_heb.name_hebrew, False, 100

    all_medicines = list(Medicine.objects.all())
    candidates = []
    for med in all_medicines:
        candidates.append((med.name, med))
        if med.name_hebrew:
            candidates.append((med.name_hebrew, med))

    if not candidates:
        return None, None, False, 0

    names_only = [c[0] for c in candidates]
    best_name, score, index = process.extractOne(
        incoming_msg, names_only, scorer=fuzz.WRatio
    )
    best_medicine = candidates[index][1]

    if score >= SIMILARITY_THRESHOLD:
        return best_medicine, best_name, True, score
    else:
        return None, None, False, score


@csrf_exempt
def whatsapp_bot(request):
    if request.method == 'POST':

        incoming_msg = request.POST.get('Body', '').strip()
        sender_phone = request.POST.get('From', '')

        response = MessagingResponse()
        msg = response.message()

        # ── First time user
        visitor, is_new = Visitor.objects.get_or_create(phone=sender_phone)
        if is_new:
            msg.body(get_welcome_message())
            return HttpResponse(str(response), content_type='text/xml')
        
        # ── Check for image
        num_media = int(request.POST.get('NumMedia', 0))
        if num_media > 0:
            image_url = request.POST.get('MediaUrl0', '')

            msg.body(
                "📸 קיבלתי את התמונה! מנסה לזהות את התרופה...\n"
                "📸 Got your image! Trying to identify the medicine..."
            )

            # Identify medicine from image
            identified_name = identify_medicine_from_image(image_url)

            if identified_name:
                # Search in database
                medicine, matched_name, is_fuzzy, score = search_medicine(
                    identified_name
                )

                if medicine and not is_fuzzy:
                    heb = f" ({medicine.name_hebrew})" if medicine.name_hebrew else ""
                    details = []
                    if medicine.expiry_date:
                        from django.utils import timezone
                        if medicine.is_expired():
                            details.append(f"⚠️ פג תוקף! EXPIRED: {medicine.expiry_date.strftime('%d/%m/%Y')}")
                        else:
                            details.append(f"📅 תוקף עד | Expiry: {medicine.expiry_date.strftime('%d/%m/%Y')}")
                    if medicine.min_age:
                        details.append(f"👶 מגיל | Min age: {medicine.min_age}+")
                    if medicine.suitable_pregnant:
                        details.append(f"🤰 מתאים להריון | Safe for pregnant: ✅")
                    else:
                        details.append(f"🤰 מתאים להריון | Safe for pregnant: ❌")
                    details_text = "\n".join(details)

                    if medicine.quantity > 0 and not medicine.is_expired():
                        response2 = MessagingResponse()
                        msg2 = response2.message()
                        msg2.body(
                            f"🔍 זיהיתי: *{identified_name}*\n\n"
                            f"✅ *{medicine.name}{heb}* זמינה! | Available! 🙏\n\n"
                            f"כמות | Quantity: *{medicine.quantity} units*\n\n"
                            f"{details_text}\n\n"
                            f"אנא צור/י קשר לתיאום איסוף.\n"
                            f"Please contact us to arrange pickup."
                        )
                        return HttpResponse(
                            str(response2), content_type='text/xml'
                        )
                    else:
                        response2 = MessagingResponse()
                        msg2 = response2.message()
                        msg2.body(
                            f"🔍 זיהיתי: *{identified_name}*\n\n"
                            f"😔 התרופה אזלה מהמלאי.\n"
                            f"Out of stock.\n\n"
                            f"{details_text}"
                        )
                        return HttpResponse(
                            str(response2), content_type='text/xml'
                        )

                elif medicine and is_fuzzy:
                    heb = f" ({medicine.name_hebrew})" if medicine.name_hebrew else ""
                    response2 = MessagingResponse()
                    msg2 = response2.message()
                    msg2.body(
                        f"🔍 זיהיתי: *{identified_name}*\n\n"
                        f"🤔 האם התכוונת ל: *{medicine.name}{heb}*?\n"
                        f"Did you mean: *{medicine.name}{heb}*?\n\n"
                        f"שלח/י את השם לאישור. Send the name to confirm."
                    )
                    return HttpResponse(
                        str(response2), content_type='text/xml'
                    )

                else:
                    # Not in DB — get AI suggestions
                    available_medicines = list(Medicine.objects.all())
                    ai_suggestions = get_ai_suggestions(
                        identified_name, available_medicines
                    )
                    response2 = MessagingResponse()
                    msg2 = response2.message()
                    if ai_suggestions:
                        msg2.body(
                            f"🔍 זיהיתי: *{identified_name}*\n\n"
                            f"❌ לא נמצא במאגר שלנו.\n"
                            f"Not in our Gemach.\n\n"
                            f"{ai_suggestions}"
                        )
                    else:
                        msg2.body(
                            f"🔍 זיהיתי: *{identified_name}*\n\n"
                            f"❌ לא נמצא במאגר שלנו.\n"
                            f"Not found in our Gemach.\n\n"
                            + get_medicine_list()
                        )
                    return HttpResponse(
                        str(response2), content_type='text/xml'
                    )

            else:
                # Could not identify
                response2 = MessagingResponse()
                msg2 = response2.message()
                msg2.body(
                    "😔 לא הצלחתי לזהות תרופה בתמונה.\n"
                    "Could not identify a medicine in this image.\n\n"
                    "אנא שלח/י תמונה ברורה יותר של קופסת התרופה,\n"
                    "או הקלד/י את שם התרופה ישירות.\n\n"
                    "Please send a clearer photo of the medicine box,\n"
                    "or type the medicine name directly."
                )
                return HttpResponse(
                    str(response2), content_type='text/xml'
                )

        # ── LIST command
        if incoming_msg.upper() in ['LIST', 'רשימה']:
            msg.body(get_medicine_list())
            return HttpResponse(str(response), content_type='text/xml')

        # ── Natural language detection
        if is_natural_language(incoming_msg):
            all_medicines = list(Medicine.objects.all())
            nl_result = get_natural_language_medicines(
                incoming_msg, all_medicines
            )
            if nl_result:
                msg.body(nl_result)
                return HttpResponse(str(response), content_type='text/xml')
            else:
                msg.body(
                    f"🤔 לא מצאתי תרופות מתאימות לבקשה שלך.\n"
                    f"🤔 No matching medicines found for your request.\n\n"
                    + get_medicine_list()
                )
                return HttpResponse(str(response), content_type='text/xml')

        # ── Regular medicine search
        medicine, matched_name, is_fuzzy, score = search_medicine(incoming_msg)

        if medicine and not is_fuzzy:
            heb = f" ({medicine.name_hebrew})" if medicine.name_hebrew else ""

            # ── Build details string
            details = []

            if medicine.expiry_date:
                from django.utils import timezone
                if medicine.is_expired():
                    details.append(
                        f"⚠️ פג תוקף! | ⚠️ EXPIRED: "
                        f"{medicine.expiry_date.strftime('%d/%m/%Y')}"
                    )
                else:
                    details.append(
                        f"📅 תוקף עד | Expiry: "
                        f"{medicine.expiry_date.strftime('%d/%m/%Y')}"
                    )

            if medicine.min_age:
                details.append(
                    f"👶 מגיל | Min age: {medicine.min_age}+"
                )

            if medicine.suitable_pregnant:
                details.append(
                    f"🤰 מתאים להריון | Safe for pregnant: ✅"
                )
            else:
                details.append(
                    f"🤰 מתאים להריון | Safe for pregnant: ❌"
                )

            details_text = "\n".join(details)

            if medicine.is_expired():
                msg.body(
                    f"⚠️ *{medicine.name}{heb}*\n\n"
                    f"התרופה פגה! אנא פנה אלינו ישירות.\n"
                    f"This medicine is EXPIRED. Please contact us.\n\n"
                    f"{details_text}"
                )

            elif medicine.quantity == 0:
                msg.body(
                    f"😔 *{medicine.name}{heb}*\n\n"
                    f"התרופה נמצאת במאגר אך אזלה מהמלאי.\n"
                    f"Out of stock. Please contact us directly. 🙏\n\n"
                    f"{details_text}"
                )

            elif medicine.quantity <= 2:
                msg.body(
                    f"⚠️ *{medicine.name}{heb}* — כמות נמוכה!\n"
                    f"⚠️ *{medicine.name}{heb}* — Low stock!\n\n"
                    f"כמות | Quantity: *{medicine.quantity} units*\n\n"
                    f"{details_text}\n\n"
                    f"אנא צור/י קשר בהקדם. Contact us soon! 🙏"
                )
                notify_admin_low_stock(medicine)

            else:
                msg.body(
                    f"✅ *{medicine.name}{heb}* זמינה! | Available! 🙏\n\n"
                    f"כמות | Quantity: *{medicine.quantity} units*\n\n"
                    f"{details_text}\n\n"
                    f"אנא צור/י קשר לתיאום איסוף.\n"
                    f"Please contact us to arrange pickup."
                )

        elif medicine and is_fuzzy:
            heb = f" ({medicine.name_hebrew})" if medicine.name_hebrew else ""
            msg.body(
                f"🤔 לא מצאתי *{incoming_msg}* בגמ\"ח.\n"
                f"🤔 I didn't find *{incoming_msg}*.\n\n"
                f"האם התכוונת ל: *{medicine.name}{heb}*?\n"
                f"Did you mean: *{medicine.name}{heb}*?\n\n"
                f"שלח/י את השם המדויק לבדיקה חוזרת.\n"
                f"Reply with the correct name to check again."
            )
            notify_admin(
                medicine_searched=incoming_msg,
                requester_phone=sender_phone,
                suggestion=medicine.name
            )

        else:
            # ── Get AI suggestions
            available_medicines = list(Medicine.objects.all())
            ai_suggestions = get_ai_suggestions(
                incoming_msg, available_medicines
            )

            if ai_suggestions:
                msg.body(
                    f"❌ לא נמצאה *{incoming_msg}* במאגר שלנו.\n"
                    f"❌ *{incoming_msg}* was not found in our Gemach.\n\n"
                    f"{ai_suggestions}\n\n"
                    f"שלח/י שם תרופה לבדיקת זמינות.\n"
                    f"Send a medicine name to check availability."
                )
            else:
                msg.body(
                    f"❌ לא נמצאה *{incoming_msg}* במאגר שלנו.\n"
                    f"❌ *{incoming_msg}* was not found in our Gemach.\n\n"
                    + get_medicine_list()
                )

            notify_admin(
                medicine_searched=incoming_msg,
                requester_phone=sender_phone,
                suggestion=None
            )

        return HttpResponse(str(response), content_type='text/xml')

@csrf_exempt
def sms_bot(request):
    if request.method == 'POST':

        incoming_msg = request.POST.get('Body', '').strip()
        sender_phone = request.POST.get('From', '')

        response = MessagingResponse()

        # ── LIST command
        if incoming_msg.upper() in ['LIST', 'רשימה']:
            response.message(get_medicine_list())
            return HttpResponse(str(response), content_type='text/xml')

        # ── Search
        medicine, matched_name, is_fuzzy, score = search_medicine(incoming_msg)

        if medicine and not is_fuzzy:
            heb = f" ({medicine.name_hebrew})" if medicine.name_hebrew else ""
            if medicine.quantity == 0:
                response.message(
                    f"מצטערים, {medicine.name}{heb} נמצאת במאגר אך אזלה מהמלאי.\n"
                    f"Sorry, {medicine.name}{heb} is out of stock.\n"
                    f"צרו קשר ישירות לבירור. Please contact us directly."
                )
            elif medicine.quantity <= 2:
                response.message(
                    f"זהירות! {medicine.name}{heb} זמינה אך כמות נמוכה ({medicine.quantity} יחידות).\n"
                    f"Warning! {medicine.name}{heb} available but low stock ({medicine.quantity} units).\n"
                    f"צרו קשר בהקדם. Contact us soon."
                )
                notify_admin_low_stock(medicine)
            else:
                response.message(
                    f"כן! {medicine.name}{heb} זמינה בגמ\"ח ({medicine.quantity} יחידות).\n"
                    f"Yes! {medicine.name}{heb} is available ({medicine.quantity} units).\n"
                    f"צרו קשר לתיאום. Contact us to arrange pickup."
                )

        elif medicine and is_fuzzy:
            heb = f" ({medicine.name_hebrew})" if medicine.name_hebrew else ""
            response.message(
                f"לא מצאתי {incoming_msg}.\n"
                f"האם התכוונת ל: {medicine.name}{heb}?\n"
                f"Did you mean: {medicine.name}{heb}?\n"
                f"שלח/י את השם המדויק. Reply with the correct name."
            )
            notify_admin(
                medicine_searched=incoming_msg,
                requester_phone=sender_phone,
                suggestion=medicine.name
            )

        else:
            response.message(
                f"לא נמצא {incoming_msg} במאגר שלנו.\n"
                f"{incoming_msg} not found in our Gemach.\n\n"
                + get_medicine_list()
            )
            notify_admin(
                medicine_searched=incoming_msg,
                requester_phone=sender_phone,
                suggestion=None
            )

        return HttpResponse(str(response), content_type='text/xml')




def get_ai_suggestions(medicine_name, available_medicines):
    """
    Ask Claude AI to suggest alternatives from our available medicines.
    """
    try:
        client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )

        # Build list of available medicines
        medicines_list = "\n".join([
            f"- {m.name}"
            + (f" ({m.name_hebrew})" if m.name_hebrew else "")
            + f" — {m.quantity} units"
            for m in available_medicines
            if m.quantity > 0 and not m.is_expired()
        ])

        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a helpful pharmacy assistant for a medicine charity (גמ"ח תרופות) in Israel.

                The user is looking for: {medicine_name}
                This medicine is NOT available in our inventory.

                Our currently available medicines are:
                {medicines_list}

                Please suggest 2-3 alternatives from OUR LIST ONLY that could serve a similar purpose.
                Be brief and practical.
                Reply in both Hebrew and English.
                Format exactly like this:
                🤖 הצעות חלופיות | AI Suggestions:
                - [medicine name] — [one line reason in Hebrew] | [one line reason in English]
                - [medicine name] — [one line reason in Hebrew] | [one line reason in English]

                If no relevant alternatives exist in our list, reply with exactly:
                NO_ALTERNATIVES"""
                                }
                            ]
                        )

        result = message.content[0].text.strip()

        if result == "NO_ALTERNATIVES":
            return None

        return result

    except Exception as e:
        print(f"Claude API error: {e}")
        return None
    
def get_natural_language_medicines(user_query, all_medicines):
    """
    Use Claude AI to understand natural language queries
    and match them to medicines in our database.
    """
    try:
        client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )

        # Build full medicine list
        medicines_list = "\n".join([
            f"- {m.name}"
            + (f" ({m.name_hebrew})" if m.name_hebrew else "")
            + f" — quantity: {m.quantity}"
            + (" — EXPIRED" if m.is_expired() else "")
            for m in all_medicines
        ])

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a helpful pharmacy assistant for a medicine charity (גמ"ח תרופות) in Israel.

The user wrote a natural language query (in Hebrew or English):
"{user_query}"

Our medicine inventory:
{medicines_list}

Task:
1. Understand what condition or symptom the user is describing
2. Find ALL relevant medicines from OUR LIST ONLY that could help
3. Only suggest medicines with quantity > 0 and not expired

Reply in both Hebrew and English using EXACTLY this format:
🔍 הבנתי שאתה מחפש | I understood you need: [condition in Hebrew | condition in English]

💊 תרופות זמינות | Available medicines:
- [medicine name] ([name_hebrew]) — [brief reason Hebrew] | [brief reason English]
- [medicine name] ([name_hebrew]) — [brief reason Hebrew] | [brief reason English]

If no relevant medicines found, reply exactly:
NO_MATCH"""
                }
            ]
        )

        result = message.content[0].text.strip()

        if result == "NO_MATCH":
            return None

        return result

    except Exception as e:
        print(f"Claude NL error: {e}")
        return None
    

def is_natural_language(text):
    """
    Detect if the user is writing a natural language query
    rather than a specific medicine name.
    """
    natural_language_keywords = [
        # Hebrew keywords
        'משהו', 'תרופה', 'כאב', 'לכאב', 'כואב', 'חום',
        'שיעול', 'נזלת', 'אלרגיה', 'עייפות', 'סחרחורת',
        'בחילה', 'הקאה', 'שלשול', 'עצירות', 'צרבת',
        'גירוד', 'פריחה', 'זיהום', 'דלקת', 'נפיחות',
        'לחץ דם', 'סוכר', 'כולסטרול', 'מה יש', 'יש לכם',
        'מחפש', 'מחפשת', 'צריך', 'צריכה', 'עוזר', 'עוזרת',
        # English keywords
        'something', 'medicine for', 'drug for', 'pain',
        'headache', 'fever', 'cough', 'cold', 'allergy',
        'nausea', 'diarrhea', 'constipation', 'infection',
        'inflammation', 'rash', 'itch', 'looking for',
        'do you have', 'what do you have', 'need something',
        'for my', 'help with',
    ]

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in natural_language_keywords)


def identify_medicine_from_image(image_url):
    """
    Use Claude Vision API to identify a medicine from a photo.
    Downloads image from Twilio and sends to Claude.
    """
    try:
        # ── Download image from Twilio (requires auth)
        twilio_auth = (
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        image_response = requests.get(image_url, auth=twilio_auth)

        if image_response.status_code != 200:
            print(f"Failed to download image: {image_response.status_code}")
            return None

        # ── Convert to base64
        image_data    = base64.standard_b64encode(
            image_response.content
        ).decode('utf-8')
        content_type  = image_response.headers.get(
            'Content-Type', 'image/jpeg'
        )

        # ── Send to Claude Vision
        client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type":       "base64",
                                "media_type": content_type,
                                "data":       image_data,
                            }
                        },
                        {
                            "type": "text",
                            "text": """This is a photo of a medicine box or packaging.
Please identify the medicine name.
Reply with ONLY the medicine name in English — nothing else.
For example: Ventolin
or: Acamol
If you cannot identify a medicine, reply exactly: UNKNOWN"""
                        }
                    ]
                }
            ]
        )

        result = message.content[0].text.strip()

        if result == "UNKNOWN":
            return None

        return result

    except Exception as e:
        print(f"Image identification error: {e}")
        return None