"""
Camada de Aplicação - Contém os serviços que orquestram fluxos de casos de uso.

Esta camada coordena a interação entre as entidades, repositórios e serviços da camada de domínio.
Os serviços de aplicação são responsáveis por:
1. Implementar casos de uso específicos da aplicação
2. Orquestrar chamadas entre múltiplos repositórios e serviços de domínio
3. Gerenciar transações
4. Validar entradas
5. Traduzir exceções de domínio para exceções de aplicação
6. Publicar eventos de aplicação

Principais componentes:
- Application Services: Implementam casos de uso específicos
- DTOs (Data Transfer Objects): Objetos para transferência de dados entre camadas
- Validators: Validadores de entrada
- Exceptions: Exceções específicas da camada de aplicação
""" 