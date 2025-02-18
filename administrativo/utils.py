import pandas as pd
from django.http import HttpResponse
from django.db import transaction
from django.core.exceptions import ValidationError

def export_to_excel(queryset, fields, filename):
    """
    Função genérica para exportar dados para Excel
    
    Args:
        queryset: QuerySet com os dados a serem exportados
        fields: Lista de tuplas (field_name, display_name)
        filename: Nome do arquivo a ser gerado
    """
    data = []
    for obj in queryset:
        row = {}
        for field, _ in fields:
            value = getattr(obj, field)
            row[field] = str(value) if value else ''
        data.append(row)
    
    df = pd.DataFrame(data)
    if data:  # Renomeia as colunas apenas se houver dados
        df.columns = [display_name for _, display_name in fields]
    
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    df.to_excel(response, index=False, engine='openpyxl')
    return response

def import_from_excel(file, model, fields, unique_fields):
    """
    Função genérica para importar dados do Excel
    
    Args:
        file: Arquivo Excel enviado
        model: Modelo Django para criar os objetos
        fields: Lista de campos a serem importados
        unique_fields: Lista de campos que devem ser únicos
    
    Returns:
        tuple: (sucesso, mensagem)
    """
    try:
        df = pd.read_excel(file, engine='openpyxl')
        
        # Validar colunas
        required_columns = [display_name for _, display_name in fields]
        if not all(col in df.columns for col in required_columns):
            return False, "Arquivo não contém todas as colunas necessárias"
        
        # Mapear nomes de exibição para nomes de campos
        field_map = {display_name: field_name for field_name, display_name in fields}
        
        with transaction.atomic():
            for _, row in df.iterrows():
                data = {}
                for display_name, value in row.items():
                    if display_name in field_map:
                        field_name = field_map[display_name]
                        data[field_name] = value
                
                # Verificar duplicatas
                unique_filters = {field: data[field] for field in unique_fields if field in data}
                if model.objects.filter(**unique_filters).exists():
                    continue  # Pula registros duplicados
                
                obj = model(**data)
                obj.full_clean()  # Valida o objeto
                obj.save()
        
        return True, "Importação concluída com sucesso"
    
    except ValidationError as e:
        return False, f"Erro de validação: {str(e)}"
    except Exception as e:
        return False, f"Erro ao importar: {str(e)}" 