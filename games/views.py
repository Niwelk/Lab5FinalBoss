import requests
from django.http import JsonResponse
from django.conf import settings
from .models import Game, PriceHistory
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .models import SearchHistory
from django.views.decorators.csrf import csrf_exempt
import json

API_KEY = settings.STEAM_API_KEY
@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return JsonResponse({"error": "Missing fields"}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "User exists"}, status=400)

        user = User.objects.create_user(username=username, password=password)

        return JsonResponse({"message": "User created"})

    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)
@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)

        username = data.get("username")
        password = data.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return JsonResponse({"error": "Invalid credentials"}, status=400)

        login(request, user)

        return JsonResponse({"message": "Logged in"})

    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)
@csrf_exempt
def get_search_history(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    history = SearchHistory.objects.filter(user=request.user).order_by('-date')

    result = []

    for h in history:
        result.append({
            "query": h.query,
            "date": h.date.strftime("%Y-%m-%d %H:%M")
        })

    return JsonResponse({"history": result})
@csrf_exempt
def test_api(request):
    return JsonResponse({"message": "Backend works!"})

@csrf_exempt
def search_games(request):
    query = request.GET.get('query')

    if request.user.is_authenticated:
        SearchHistory.objects.create(
            user=request.user,
            query=query
        )

    if not query:
        return JsonResponse({"error": "No query provided"}, status=400)

    url = "https://store.steampowered.com/api/storesearch/"

    params = {
        "term": query,
        "l": "english",
        "cc": "US"
    }

    try:
        response = requests.get(url, params=params, timeout=5)

        if response.status_code != 200:
            return JsonResponse({"error": "Steam API error"}, status=500)

        data = response.json()
        games = []

        for item in data.get("items", []):
            steam_id = item.get("id")

            game, _ = Game.objects.update_or_create(
                steam_id=steam_id,
                defaults={
                    "name": item.get("name"),
                    "price": item.get("price", {}).get("final", 0) / 100,
                    "image": item.get("tiny_image")
                }
            )

            games.append({
                "id": game.steam_id,
                "name": game.name,
                "price": game.price,
                "image": game.image
            })

        return JsonResponse({"games": games})

    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def game_detail(request, game_id):
    url = "https://store.steampowered.com/api/appdetails/"

    params = {
        "appids": game_id,
        "l": "english",
        "cc": "US"
    }

    try:
        response = requests.get(url, params=params, timeout=5)

        if response.status_code != 200:
            return JsonResponse({"error": "Steam API error"}, status=500)

        data = response.json()
        game_data = data.get(str(game_id), {}).get("data", {})

        if not game_data:
            return JsonResponse({"error": "Game not found"}, status=404)

        price_info = game_data.get("price_overview")

        if price_info:
            current_price = price_info.get("final", 0) / 100
        else:
            current_price = 0

        game, _ = Game.objects.update_or_create(
            steam_id=game_id,
            defaults={
                "name": game_data.get("name"),
                "price": current_price,
                "image": game_data.get("header_image")
            }
        )

        result = {
            "id": game.steam_id,
            "name": game.name,
            "description": game_data.get("short_description"),
            "image": game.image,
            "price": game.price
        }

        return JsonResponse(result)

    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def get_achievements(request, game_id):
    try:
        percent_url = "https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/"
        percent_res = requests.get(percent_url, params={"gameid": game_id}, timeout=5)

        if percent_res.status_code != 200:
            return JsonResponse({"error": "Steam API error"}, status=500)

        percent_data = percent_res.json()
        percent_list = percent_data.get("achievementpercentages", {}).get("achievements", [])

        percent_dict = {}
        for ach in percent_list:
            try:
                percent_dict[ach["name"]] = float(ach["percent"])
            except:
                percent_dict[ach["name"]] = None

        schema_url = "https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/"
        schema_res = requests.get(schema_url, params={
            "appid": game_id,
            "key": API_KEY
        }, timeout=5)

        if schema_res.status_code != 200:
            return JsonResponse({"error": "Steam API error"}, status=500)

        schema_data = schema_res.json()
        achievements_data = schema_data.get("game", {}).get("availableGameStats", {}).get("achievements", [])

        result = []

        for ach in achievements_data:
            name_key = ach.get("name")
            percent = percent_dict.get(name_key)

            result.append({
                "name": ach.get("displayName"),
                "description": ach.get("description"),
                "icon": ach.get("icon"),
                "rarity": percent,
                "category": categorize_achievement(percent)
            })

        return JsonResponse({"achievements": result})

    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def categorize_achievement(percent):
    if percent is None:
        return "unknown"
    elif percent > 50:
        return "easy"
    elif percent > 20:
        return "medium"
    elif percent > 5:
        return "rare"
    else:
        return "epic"

@csrf_exempt
def get_price(request, game_id):
    url = "https://store.steampowered.com/api/appdetails/"

    params = {
        "appids": game_id,
        "l": "english",
        "cc": "US"
    }

    try:
        response = requests.get(url, params=params, timeout=5)

        if response.status_code != 200:
            return JsonResponse({"error": "Steam API error"}, status=500)

        data = response.json()
        game_data = data.get(str(game_id), {}).get("data", {})

        if not game_data:
            return JsonResponse({"error": "Game not found"}, status=404)

        price_info = game_data.get("price_overview")

        if price_info:
            current_price = price_info.get("final", 0) / 100
            initial_price = price_info.get("initial", 0) / 100
            discount = price_info.get("discount_percent", 0)
        else:
            current_price = 0
            initial_price = 0
            discount = 0

        game, _ = Game.objects.update_or_create(
            steam_id=game_id,
            defaults={
                "name": game_data.get("name"),
                "price": current_price,
                "image": game_data.get("header_image")
            }
        )

        last = PriceHistory.objects.filter(game=game).order_by('-date').first()

        if not last or last.price != current_price:
            PriceHistory.objects.create(
                game=game,
                price=current_price
            )

        result = {
            "current_price": current_price,
            "initial_price": initial_price,
            "discount_percent": discount
        }

        return JsonResponse(result)

    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def get_price_history(request, game_id):
    try:
        game = Game.objects.get(steam_id=game_id)
        history = PriceHistory.objects.filter(game=game).order_by('date')

        result = []

        for h in history:
            result.append({
                "price": h.price,
                "date": h.date.strftime("%Y-%m-%d %H:%M")
            })

        return JsonResponse({"history": result})

    except Game.DoesNotExist:
        return JsonResponse({"error": "Game not found"}, status=404)