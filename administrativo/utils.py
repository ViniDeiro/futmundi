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
            if '__' in field:
                # Lida com campos relacionados (ex: continent__name)
                parts = field.split('__')
                value = obj
                for part in parts:
                    value = getattr(value, part)
            else:
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
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return False, f"O arquivo não contém as seguintes colunas obrigatórias: {', '.join(missing_columns)}"
        
        if df.empty:
            return False, "O arquivo está vazio. Por favor, adicione dados antes de importar."
            
        # Mapear nomes de exibição para nomes de campos
        field_map = {display_name: field_name for field_name, display_name in fields}
        
        records_created = 0
        records_skipped = 0
        
        with transaction.atomic():
            for _, row in df.iterrows():
                data = {}
                for display_name, value in row.items():
                    if display_name in field_map:
                        field_name = field_map[display_name]
                        # Remove espaços extras e converte para string se não for nulo
                        data[field_name] = str(value).strip() if pd.notnull(value) else None
                
                # Verificar duplicatas
                unique_filters = {field: data[field] for field in unique_fields if field in data}
                if model.objects.filter(**unique_filters).exists():
                    records_skipped += 1
                    continue
                
                obj = model(**data)
                obj.full_clean()  # Valida o objeto
                obj.save()
                records_created += 1
        
        message = f"{records_created} registro(s) importado(s) com sucesso."
        if records_skipped > 0:
            message += f" {records_skipped} registro(s) ignorado(s) por já existirem."
            
        return True, message
    
    except ValidationError as e:
        return False, f"Erro de validação: {str(e)}"
    except Exception as e:
        return False, f"Erro ao importar: {str(e)}" 