from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from rapidfuzz import process, fuzz
from .models import Medicine, Visitor, MissedRequest
import os

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

        # ── LIST command
        if incoming_msg.upper() in ['LIST', 'רשימה']:
            msg.body(get_medicine_list())
            return HttpResponse(str(response), content_type='text/xml')

        # ── Search
        medicine, matched_name, is_fuzzy, score = search_medicine(incoming_msg)

        if medicine and not is_fuzzy:
            heb = f" ({medicine.name_hebrew})" if medicine.name_hebrew else ""

            if medicine.quantity == 0:
                # Found in DB but out of stock
                msg.body(
                    f"😔 *{medicine.name}{heb}*\n\n"
                    f"התרופה נמצאת במאגר אך אזלה מהמלאי.\n"
                    f"This medicine is in our list but currently *out of stock*.\n\n"
                    f"אנא צור/י קשר ישירות לבירור. 🙏\n"
                    f"Please contact us directly for more info. 🙏"
                )
            elif medicine.quantity <= 2:
                # Low stock warning
                msg.body(
                    f"⚠️ *{medicine.name}{heb}* זמינה — אך כמות נמוכה!\n"
                    f"⚠️ *{medicine.name}{heb}* is available — but low stock!\n\n"
                    f"כמות נותרת | Remaining: *{medicine.quantity} units*\n\n"
                    f"אנא צור/י קשר בהקדם לתיאום איסוף. 🙏\n"
                    f"Please contact us soon to arrange pickup. 🙏"
                )
            else:
                # Fully available
                msg.body(
                    f"✅ *{medicine.name}{heb}* זמינה בגמ\"ח! 🙏\n"
                    f"✅ *{medicine.name}{heb}* is available! 🙏\n\n"
                    f"כמות נותרת | Remaining: *{medicine.quantity} units*\n\n"
                    f"אנא צור/י קשר לתיאום איסוף.\n"
                    f"Please contact us to arrange pickup."
                )

            # Alert admin if stock is low or zero
            if medicine.quantity <= 2:
                notify_admin_low_stock(medicine)

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
                medicine_searched = incoming_msg,
                requester_phone   = sender_phone,
                suggestion        = medicine.name
            )

        else:
            msg.body(
                f"❌ לא נמצאה *{incoming_msg}* במאגר שלנו.\n"
                f"❌ *{incoming_msg}* was not found in our Gemach.\n\n"
                + get_medicine_list()
            )
            notify_admin(
                medicine_searched = incoming_msg,
                requester_phone   = sender_phone,
                suggestion        = None
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