"""
lg2m/backend/app/services/image_resolver.py
Serviço de resolução e localização de figuras e diagramas das provas no disco.
Mapeia os cadernos de provas do PSC e SIS salvos em parsingScripts.
"""

import os
import glob
from pathlib import Path
from typing import Optional, Dict

class ImageResolver:
    _instance = None
    _file_index: Dict[str, str] = {}
    _initialized: bool = False

    @classmethod
    def _init_index(cls):
        if cls._initialized:
            return
        
        # Procura pastas possíveis em volta do projeto
        possible_roots = [
            Path(__file__).resolve().parent.parent.parent.parent / "parsingScripts",
            Path("/home/marcos/Projetos/LG2M/parsingScripts"),
        ]
        
        for root in possible_roots:
            if root.exists():
                for p in glob.glob(f"{root}/**/*.png", recursive=True):
                    fname = os.path.basename(p).lower()
                    if fname not in cls._file_index:
                        cls._file_index[fname] = p
        
        cls._initialized = True

    @classmethod
    def resolve_image(
        cls,
        question_id: str,
        numero_questao: Optional[int] = None,
        ano: Optional[int] = None,
        imagens_data: Optional[list] = None,
        img_index: int = 0
    ) -> Optional[str]:
        """
        Retorna o caminho absoluto do arquivo de imagem PNG no disco para a questão dada.
        """
        cls._init_index()

        # 1. Tenta correspondência direta com o nome do arquivo no JSON
        if imagens_data and isinstance(imagens_data, list) and len(imagens_data) > img_index:
            img_entry = imagens_data[img_index]
            if isinstance(img_entry, dict):
                raw_file = img_entry.get("arquivo") or ""
                fname = os.path.basename(raw_file).lower()
                if fname in cls._file_index:
                    return cls._file_index[fname]

        # 2. Busca por substring do ID da questão (ex: psc-2024-None-fisica-41 ou q41)
        q_id_lower = question_id.lower()
        for fname, fullpath in cls._file_index.items():
            if q_id_lower in fname:
                return fullpath

        # 3. Busca heurística por ano e número da questão
        if numero_questao and ano:
            patterns = [
                f"q{numero_questao:02d}",
                f"-{numero_questao:02d}_",
                f"_{numero_questao:02d}_",
                f"-{numero_questao}_",
                f"_{numero_questao}_"
            ]
            ano_str = str(ano)
            for fname, fullpath in cls._file_index.items():
                if any(p in fname for p in patterns) and (ano_str in fname or ano_str in fullpath):
                    # Evita colisão entre ex: fig01 vs questao
                    if "fig" in fname:
                        return fullpath
                    return fullpath

        return None
