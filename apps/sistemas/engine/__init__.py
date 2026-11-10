"""Motor de cálculo do Álgebra em Cena. Python puro: não importa Django (ADR-001)."""

from .equacoes import ler_sistema
from .numeros import ErroEntrada, ler_numero
from .trace import METODOS, VERSAO, resolver

__all__ = ['ErroEntrada', 'METODOS', 'VERSAO', 'ler_numero', 'ler_sistema', 'resolver']
