# План реализации фильтра категорий на странице Товаров

## Текущая ситуация

### Текущая реализация фильтрации:
1. **Фильтрация по отслеживаемым категориям работает на клиенте** (products.html:291-302)
2. Запрашивает `/api/categories?tracked=true` → получает отслеживаемые категории
3. Фильтрует только дочерние категории (`c.parent_id`)
4. Использует параметр `category_ids` в запросе товаров для фильтрации

### Проблемы текущей реализации:
1. **Неэффективная двойная выборка** - сначала категории, затем товары
2. **Нет серверной фильтрации** по `is_tracked` на уровне SQL
3. **Нет мультиселекта категорий** - только одна категория через dropdown
4. **Большинство фильтров в UI отключены** (`disabled`)

### Структура данных:
- **Таблица `categories`**: содержит поле `is_tracked` (boolean)
- **Таблица `products`**: имеет foreign key `category_id` → `categories.id`
- **API endpoint**: `/api/products` уже поддерживает `category_ids` параметр

## Детальный план реализации

### 1. Backend изменения (src/server/routes/catalog.py)

#### 1.1. Добавить параметр `tracked_only` в endpoint `/api/products`
```python
@router.get("/products", response_model=list[dict])
def list_products(
    store_code: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    category_ids: Optional[str] = Query(None, description="Comma-separated category IDs"),
    tracked_only: Optional[bool] = Query(None, description="Фильтровать только товары из отслеживаемых категорий"),
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    sort_by: str = Query("name", pattern="^(name|price|discount|last_seen)$"),
    limit: int = Query(0, description="0 = all"),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
```

#### 1.2. Реализовать логику фильтрации:
```python
if tracked_only:
    # Получаем ID отслеживаемых категорий
    tracked_cat_ids = db.query(Category.id).filter(Category.is_tracked == True).all()
    tracked_cat_ids = [c[0] for c in tracked_cat_ids]
    if tracked_cat_ids:
        query = query.filter(Product.category_id.in_(tracked_cat_ids))
    else:
        # Если нет отслеживаемых категорий - возвращаем пустой результат
        return []
```

#### 1.3. Добавить endpoint для получения дерева категорий:
```python
@router.get("/categories/tree")
def get_categories_tree(db: Session = Depends(get_db)):
    """Возвращает дерево категорий с информацией об отслеживании."""
    # Логика построения дерева с parent-child отношениями
```

### 2. Frontend изменения (src/server/templates/products.html)

#### 2.1. Заменить dropdown категорий на компонент с чекбоксами:
```html
<div class="category-filter">
    <div class="filter-header">
        <input type="checkbox" id="trackedOnly"> Только отслеживаемые категории
    </div>
    <div class="category-tree" id="categoryTree">
        <!-- Динамически загружаемое дерево с чекбоксами -->
    </div>
    <div class="filter-actions">
        <button onclick="selectAllCategories()">Выбрать все</button>
        <button onclick="deselectAllCategories()">Снять все</button>
        <button onclick="applyCategoryFilter()">Применить фильтр</button>
    </div>
</div>
```

#### 2.2. Модифицировать функцию `loadProducts()`:
```javascript
async function loadProducts() {
    // ...
    let url = `/api/products?store_code=${encodeURIComponent(activeStoreCode)}&sort_by=${sort}&limit=100`;
    
    if (document.getElementById('trackedOnly').checked) {
        url += `&tracked_only=true`;
    } else {
        const selectedCategoryIds = getSelectedCategoryIds(); // Получаем выбранные чекбоксы
        if (selectedCategoryIds.length > 0) {
            url += `&category_ids=${selectedCategoryIds.join(',')}`;
        }
    }
    // ...
}
```

#### 2.3. Компонент дерева категорий:
- Загружать данные через `/api/categories/tree`
- Отображать иерархию с отступами для дочерних элементов
- Показывать статус `is_tracked` (например, звёздочкой или цветом)
- Реализовать чекбоксы с тремя состояниями (checked, indeterminate, unchecked)

### 3. Логика выборки категорий

#### 3.1. Хранение состояния:
```javascript
let selectedCategoryIds = [];
let categoryTreeData = null;

function updateSelectedCategoryIds() {
    selectedCategoryIds = Array.from(document.querySelectorAll('.category-checkbox:checked'))
        .map(cb => parseInt(cb.value));
}
```

#### 3.2. Применение фильтра:
```javascript
function applyCategoryFilter() {
    updateSelectedCategoryIds();
    loadProducts();
}
```

### 4. Улучшения UX

#### 4.1. Сохранение состояния в localStorage:
```javascript
function saveFilterState() {
    localStorage.setItem('categoryFilter_selectedIds', JSON.stringify(selectedCategoryIds));
    localStorage.setItem('categoryFilter_trackedOnly', document.getElementById('trackedOnly').checked);
}

function loadFilterState() {
    const savedIds = localStorage.getItem('categoryFilter_selectedIds');
    const trackedOnly = localStorage.getItem('categoryFilter_trackedOnly');
    if (savedIds) selectedCategoryIds = JSON.parse(savedIds);
    if (trackedOnly) document.getElementById('trackedOnly').checked = trackedOnly === 'true';
}
```

#### 4.2. Счетчик выбранных категорий:
```html
<span id="selectedCount" style="margin-left: 10px; color: #666;">Выбрано: 0</span>
```

#### 4.3. Поиск по названию категории:
```html
<input type="text" id="categorySearch" placeholder="Поиск категории..." 
       oninput="filterCategoryTree(this.value)">
```

### 5. Приоритеты реализации

#### Приоритет 1 (Основной функционал):
1. Добавить параметр `tracked_only` в backend
2. Реализовать дерево категорий с чекбоксами в UI
3. Модифицировать `loadProducts()` для поддержки множественного выбора

#### Приоритет 2 (Улучшения UX):
1. Сохранение состояния фильтров в localStorage
2. Счетчик выбранных категорий
3. Поиск по названию категории в дереве
4. Кнопки "Развернуть/свернуть все" для дерева

#### Приоритет 3 (Оптимизации):
1. Кэширование дерева категорий на клиенте
2. Виртуализация для большого количества категорий
3. Preload категорий при загрузке страницы

### 6. Тестирование

#### 6.1. Backend тесты:
- `/api/products?tracked_only=true` возвращает только товары из категорий с `is_tracked=True`
- `/api/products?category_ids=1,2,3` работает корректно
- `tracked_only` имеет приоритет над `category_ids`

#### 6.2. Frontend тесты:
- Чекбоксы корректно отправляют запросы
- Состояние сохраняется при перезагрузке
- Дерево категорий отображает статус `is_tracked`
- Мультиселект работает корректно

### 7. Временная оценка

- **Backend изменения**: 2-3 часа
- **Frontend компонент**: 4-5 часов  
- **Тестирование и отладка**: 2-3 часа
- **Итого**: 8-11 часов

### 8. Критические моменты

1. **Порядок endpoint'ов**: Не нарушать порядок в catalog.py (stats должен быть до product_id)
2. **Миграции**: Не требуются, т.к. структура данных не меняется
3. **Rate limiting**: Добавить дебаунс на клиенте для предотвращения DDOS API
4. **Производительность**: Использовать `JOIN` вместо подзапросов при фильтрации по отслеживаемым категориям
5. **Обратная совместимость**: Существующий dropdown категорий должен продолжать работать

### 9. Структура изменений

#### Файлы для изменения:
1. `src/server/routes/catalog.py` - backend изменения
2. `src/server/templates/products.html` - frontend изменения
3. `src/server/models.py` - возможно, добавить методы для работы с деревом

#### Новые компоненты:
1. `CategoryTree` компонент с чекбоксами
2. `CategoryFilter` компонент с настройками фильтрации
3. Утилиты для работы с localStorage

### 10. Риски и митигация

#### Риск 1: Производительность при большом количестве категорий
- **Митигация**: Реализовать ленивую загрузку дерева, виртуализацию

#### Риск 2: Сложность поддержки иерархического дерева
- **Митигация**: Использовать рекурсивный алгоритм для построения дерева

#### Риск 3: Конфликты с существующими фильтрами
- **Митигация**: Тщательно тестировать все комбинации фильтров

### 11. Критерии успеха

1. Пользователи могут выбирать одну или несколько категорий через чекбоксы
2. Фильтрация работает на сервере (не на клиенте)
3. Производительность улучшена по сравнению с текущей реализацией
4. Интерфейс интуитивно понятен
5. Состояние фильтров сохраняется между сессиями