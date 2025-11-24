Добавить студента  
`POST /students/add`

Удалить студента по ID  
`DELETE /students/delete/{student_id}`

Удалить студентов по статусу  
`DELETE /students/delete_by_status/{status}`

Обновить данные студента  
`PATCH /students/update/{student_id}`

Фильтрация студентов  
`GET /students/filter`   
Поддерживаемые фильтры:    
            -born_after / born_before - диапазон дат рождения  
            -group, last_name - точное совпадение  
            -has_email - есть ли email в контактах  
            -score_present - есть ли оценка с конкретным значением  
            -offset / limit - пагинация  

Добавить оценку  
`POST /grades/add`  

Удалить оценку  
`DELETE /grades/delete/{grade_id}`

Для запуска выполнить:
```
docker compose exec app python init_db.py
docker compose up -d --build
```
