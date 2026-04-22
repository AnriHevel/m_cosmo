"""
Скрипт для получения категорий с cosmetic.magnit.ru через API
"""
import requests
import json
import time

# Корневые категории cosmetic.magnit.ru (из URL)
root_categories = [
    {'id': 100650, 'title': 'Макияж'},
    {'id': 100651, 'title': 'Уход'},
    {'id': 100652, 'title': 'Волосы'},
    {'id': 37061, 'title': 'Парфюмерия'},
    {'id': 100648, 'title': 'Для дома и питомцев'},
    {'id': 100653, 'title': 'Детям'},
    {'id': 100654, 'title': 'На все случаи'},
    {'id': 100682, 'title': 'Для мужчин'},
]

store_code = '932177'
store_type = '3'

url = 'https://cosmetic.magnit.ru/webgate/v2/goods/search'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Referer': 'https://cosmetic.magnit.ru/',
    'Origin': 'https://cosmetic.magnit.ru',
    'X-Client-Name': 'cosmetic',
    'X-New-Magnit': 'true',
    'X-Device-Platform': 'Web'
}

session = requests.Session()
print('Получаем cookies...')
session.get('https://cosmetic.magnit.ru/', timeout=10)
time.sleep(1)

all_categories = []

print('\n' + '='*70)
print('Сбор категорий с cosmetic.magnit.ru')
print('='*70 + '\n')

for cat in root_categories:
    payload = {
        'sort': {'order': 'desc', 'type': 'popularity'},
        'pagination': {'limit': 1, 'offset': 0},
        'includeAdultGoods': True,
        'storeCode': store_code,
        'storeType': store_type,
        'catalogType': '1',
        'categories': [cat['id']]
    }
    
    try:
        response = session.post(url, json=payload, headers=headers, timeout=15)
        data = response.json()
        
        category_data = data.get('category', {})
        if category_data:
            root_id = category_data.get('id')
            root_title = category_data.get('title')
            subcats = data.get('fastCategoriesExtended', [])
            
            print(f'[OK] {root_title} (ID: {root_id})')
            print(f'  Подкатегорий: {len(subcats)}')
            for sub in subcats:
                sub_title = sub.get('title')
                sub_id = sub.get('id')
                print(f'    - {sub_title} (ID: {sub_id})')
            
            all_categories.append({
                'id': root_id,
                'title': root_title,
                'subcategories': [{'id': s['id'], 'title': s['title']} for s in subcats if s.get('id') and s.get('title')]
            })
        else:
            print(f'[!] Категория {cat["title"]} не найдена в API')
            
    except Exception as e:
        print(f'[ERROR] {cat["title"]}: {e}')
    
    time.sleep(0.5)

print(f'\n[OK] Всего получено {len(all_categories)} категорий')

# Сохраняем в JSON
output_file = 'D:\\pythonProjects\\m_cosmo\\src\\data\\cosmetic_categories.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_categories, f, ensure_ascii=False, indent=2)
print(f'[OK] Сохранено в {output_file}')

# Сохраняем в БД
print('\nСохраняем в базу данных...')
import sys
sys.path.insert(0, 'D:\\pythonProjects\\m_cosmo')
from src.server.database import SessionLocal
from src.server.models import Category

db = SessionLocal()
try:
    # Очищаем таблицу
    print('Очищаем таблицу categories...')
    db.query(Category).delete()
    db.commit()
    print('[OK] Таблица очищена')
    
    # Добавляем новые категории
    total = 0
    for cat_data in all_categories:
        # Корневая категория
        root = Category(
            magnit_id=cat_data['id'],
            name=cat_data['title'],
            url='',
            parent_id=None,
            is_tracked=False,
            product_count=0
        )
        db.add(root)
        db.flush()
        total += 1
        print(f'[OK] Добавлена корневая: {cat_data["title"]} (ID: {cat_data["id"]})')
        
        # Подкатегории
        for sub in cat_data['subcategories']:
            sub_cat = Category(
                magnit_id=sub['id'],
                name=sub['title'],
                url='',
                parent_id=root.id,
                is_tracked=False,
                product_count=0
            )
            db.add(sub_cat)
            total += 1
            print(f'  [OK] Подкатегория: {sub["title"]}')
    
    db.commit()
    print(f'\n[OK] Всего добавлено: {total} категорий')
    
except Exception as e:
    db.rollback()
    print(f'[ERROR] Ошибка при сохранении: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()

print('\n' + '='*70)
print('Готово!')
print('='*70)
