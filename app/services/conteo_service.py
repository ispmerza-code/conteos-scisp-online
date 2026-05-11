from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from app.models.models import Conteo, ConteoDetalles, Usuarios, Sucursales, Catalogo
from app.schemas.schemas import (
    ConteoCreate, ConteoAsignar, ConteoEdit, ConteoContestar,
    ConteoResponse, ConteoListResponse, ConteoDetalleCreate
)

class ConteoService:
    
    @staticmethod
    def crear_conteo(
        db: Session,
        conteo_data: ConteoCreate,
        user_id: int
    ) -> ConteoResponse:
        """Crear un nuevo conteo"""
        
        # Verificar que la sucursal existe
        sucursal = db.query(Sucursales).filter(Sucursales.IdCentro == conteo_data.IdCentro).first()
        if not sucursal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sucursal {conteo_data.IdCentro} no encontrada"
            )
        
        # Verificar que todos los productos existen
        codigos_barras = [detalle.CodigoBarras for detalle in conteo_data.detalles]
        productos_existentes = db.query(Catalogo.CodigoBarras).filter(
            Catalogo.CodigoBarras.in_(codigos_barras)
        ).all()
        productos_existentes = [p[0] for p in productos_existentes]
        
        productos_no_encontrados = set(codigos_barras) - set(productos_existentes)
        if productos_no_encontrados:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Productos no encontrados: {', '.join(productos_no_encontrados)}"
            )
        
        # Crear el conteo principal
        nuevo_conteo = Conteo(
            Fechal=date.today(),
            Envio=1,  # Por defecto finalizado al crear
            IdRealizo=user_id,
            IdCentro=conteo_data.IdCentro,
            IdUsuario=user_id  # Mismo usuario que lo crea
        )
        
        db.add(nuevo_conteo)
        db.flush()  # Para obtener el ID
        
        # Crear los detalles del conteo
        for detalle in conteo_data.detalles:
            nuevo_detalle = ConteoDetalles(
                IdConteo=nuevo_conteo.idConteo,
                CodigoBarras=detalle.CodigoBarras,
                NSistema=detalle.NSistema,
                NExcistencia=detalle.NExcistencia,
                Precio=detalle.Precio
            )
            db.add(nuevo_detalle)
        
        db.commit()
        db.refresh(nuevo_conteo)
        
        return ConteoService._build_conteo_response(db, nuevo_conteo)
    
    @staticmethod
    def asignar_conteo(
        db: Session,
        conteo_data: ConteoAsignar,
        user_id: int
    ) -> ConteoResponse:
        """Asignar un conteo a otro usuario"""
        
        # Verificar que el usuario asignado existe
        usuario_asignado = db.query(Usuarios).filter(
            Usuarios.IdUsuarios == conteo_data.IdUsuario,
            Usuarios.Estatus == 1
        ).first()
        if not usuario_asignado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario {conteo_data.IdUsuario} no encontrado o inactivo"
            )
        
        # Verificar que la sucursal existe
        sucursal = db.query(Sucursales).filter(Sucursales.IdCentro == conteo_data.IdCentro).first()
        if not sucursal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sucursal {conteo_data.IdCentro} no encontrada"
            )
        
        # Verificar que todos los productos existen
        codigos_barras = [detalle.CodigoBarras for detalle in conteo_data.detalles]
        productos_existentes = db.query(Catalogo.CodigoBarras).filter(
            Catalogo.CodigoBarras.in_(codigos_barras)
        ).all()
        productos_existentes = [p[0] for p in productos_existentes]
        
        productos_no_encontrados = set(codigos_barras) - set(productos_existentes)
        if productos_no_encontrados:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Productos no encontrados: {', '.join(productos_no_encontrados)}"
            )
        
        # Validar que la fecha no sea anterior a hoy
        fecha_conteo = conteo_data.Fechal or date.today()
        if fecha_conteo < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha del conteo no puede ser anterior a hoy"
            )
        
        # Crear el conteo asignado
        nuevo_conteo = Conteo(
            Fechal=fecha_conteo,
            Envio=0,  # Pendiente porque se asigna
            IdRealizo=user_id,
            IdCentro=conteo_data.IdCentro,
            IdUsuario=conteo_data.IdUsuario  # Usuario asignado
        )
        
        db.add(nuevo_conteo)
        db.flush()
        
        # Crear los detalles del conteo
        for detalle in conteo_data.detalles:
            nuevo_detalle = ConteoDetalles(
                IdConteo=nuevo_conteo.idConteo,
                CodigoBarras=detalle.CodigoBarras,
                NSistema=detalle.NSistema,
                NExcistencia=detalle.NExcistencia,
                Precio=detalle.Precio
            )
            db.add(nuevo_detalle)
        
        db.commit()
        db.refresh(nuevo_conteo)
        
        return ConteoService._build_conteo_response(db, nuevo_conteo)
    
    @staticmethod
    def editar_conteo(
        db: Session,
        conteo_id: int,
        conteo_data: ConteoEdit,
        user_id: int
    ) -> ConteoResponse:
        """Editar un conteo existente"""
        
        # Obtener el conteo
        conteo = db.query(Conteo).filter(Conteo.idConteo == conteo_id).first()
        if not conteo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conteo no encontrado"
            )
        
        # Verificar que el conteo esté pendiente (Envio = 0)
        if conteo.Envio == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede editar un conteo que ya ha sido finalizado"
            )
        
        # Actualizar campos del conteo principal
        if conteo_data.Fechal is not None:
            if conteo_data.Fechal < date.today():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La fecha del conteo no puede ser anterior a hoy"
                )
            conteo.Fechal = conteo_data.Fechal
        
        if conteo_data.IdCentro is not None:
            sucursal = db.query(Sucursales).filter(Sucursales.IdCentro == conteo_data.IdCentro).first()
            if not sucursal:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sucursal {conteo_data.IdCentro} no encontrada"
                )
            conteo.IdCentro = conteo_data.IdCentro
        
        if conteo_data.IdUsuario is not None:
            usuario = db.query(Usuarios).filter(
                Usuarios.IdUsuarios == conteo_data.IdUsuario,
                Usuarios.Estatus == 1
            ).first()
            if not usuario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Usuario {conteo_data.IdUsuario} no encontrado o inactivo"
                )
            conteo.IdUsuario = conteo_data.IdUsuario
        
        # Actualizar detalles si se proporcionan
        if conteo_data.detalles is not None:
            # Eliminar detalles existentes
            db.query(ConteoDetalles).filter(ConteoDetalles.IdConteo == conteo_id).delete()
            
            # Verificar que todos los productos existen
            codigos_barras = [detalle.CodigoBarras for detalle in conteo_data.detalles]
            productos_existentes = db.query(Catalogo.CodigoBarras).filter(
                Catalogo.CodigoBarras.in_(codigos_barras)
            ).all()
            productos_existentes = [p[0] for p in productos_existentes]
            
            productos_no_encontrados = set(codigos_barras) - set(productos_existentes)
            if productos_no_encontrados:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Productos no encontrados: {', '.join(productos_no_encontrados)}"
                )
            
            # Crear nuevos detalles
            for detalle in conteo_data.detalles:
                nuevo_detalle = ConteoDetalles(
                    IdConteo=conteo_id,
                    CodigoBarras=detalle.CodigoBarras,
                    NSistema=detalle.NSistema,
                    NExcistencia=detalle.NExcistencia,
                    Precio=detalle.Precio
                )
                db.add(nuevo_detalle)
        
        db.commit()
        db.refresh(conteo)
        
        return ConteoService._build_conteo_response(db, conteo)
    
    @staticmethod
    def contestar_conteo(
        db: Session,
        conteo_id: int,
        conteo_data: ConteoContestar,
        user_id: int
    ) -> ConteoResponse:
        """Contestar un conteo (actualizar existencias físicas)"""
        
        # Obtener el conteo
        conteo = db.query(Conteo).filter(Conteo.idConteo == conteo_id).first()
        if not conteo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conteo no encontrado"
            )
        
        # Verificar que el conteo esté pendiente
        if conteo.Envio == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este conteo ya ha sido contestado"
            )
        
        # Actualizar existencias físicas
        for detalle_update in conteo_data.detalles:
            if detalle_update.NExcistencia is not None:
                # Buscar el detalle por código de barras
                detalle = db.query(ConteoDetalles).filter(
                    and_(
                        ConteoDetalles.IdConteo == conteo_id,
                        ConteoDetalles.CodigoBarras == detalle_update.CodigoBarras
                    )
                ).first()
                
                if detalle:
                    detalle.NExcistencia = detalle_update.NExcistencia
        
        # Marcar el conteo como finalizado
        conteo.Envio = 1
        
        db.commit()
        db.refresh(conteo)
        
        return ConteoService._build_conteo_response(db, conteo)
    
    @staticmethod
    def eliminar_conteo(db: Session, conteo_id: int, user_id: int) -> dict:
        """Eliminar un conteo (solo administradores)"""
        
        conteo = db.query(Conteo).filter(Conteo.idConteo == conteo_id).first()
        if not conteo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conteo no encontrado"
            )
        
        # Eliminar detalles primero (por las llaves foráneas)
        db.query(ConteoDetalles).filter(ConteoDetalles.IdConteo == conteo_id).delete()
        
        # Eliminar el conteo
        db.delete(conteo)
        db.commit()
        
        return {"message": f"Conteo {conteo_id} eliminado exitosamente"}
    
    @staticmethod
    def obtener_conteo(
        db: Session,
        conteo_id: int,
        allowed_centros: Optional[List[str]] = None
    ) -> ConteoResponse:
        """Obtener un conteo por ID.
        Si allowed_centros no es None, verifica que el conteo pertenezca a una sucursal permitida.
        """
        conteo = db.query(Conteo).filter(Conteo.idConteo == conteo_id).first()
        if not conteo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conteo no encontrado"
            )

        if allowed_centros is not None and conteo.IdCentro not in allowed_centros:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a este conteo"
            )

        return ConteoService._build_conteo_response(db, conteo)
    
    @staticmethod
    def listar_conteos(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        id_centro: Optional[str] = None,
        envio: Optional[int] = None,
        id_usuario: Optional[int] = None,
        allowed_centros: Optional[List[str]] = None
    ) -> List[ConteoListResponse]:
        """Listar conteos con filtros opcionales.
        allowed_centros: si no es None, restringe a esas sucursales (usuarios nivel 2 y 4).
        """
        query = db.query(Conteo)

        # Restricción de sucursales para niveles con acceso limitado
        if allowed_centros is not None:
            query = query.filter(Conteo.IdCentro.in_(allowed_centros))

        if id_centro:
            query = query.filter(Conteo.IdCentro == id_centro)

        if envio is not None:
            query = query.filter(Conteo.Envio == envio)

        if id_usuario:
            query = query.filter(Conteo.IdUsuario == id_usuario)

        query = query.order_by(Conteo.Fechal.desc(), Conteo.idConteo.desc())
        
        conteos = query.offset(skip).limit(limit).all()
        
        result = []
        for conteo in conteos:
            # Contar productos en cada conteo
            total_productos = db.query(ConteoDetalles).filter(
                ConteoDetalles.IdConteo == conteo.idConteo
            ).count()
            
            result.append(ConteoListResponse(
                idConteo=conteo.idConteo,
                Fechal=conteo.Fechal,
                Envio=conteo.Envio,
                IdRealizo=conteo.IdRealizo,
                IdCentro=conteo.IdCentro,
                IdUsuario=conteo.IdUsuario,
                total_productos=total_productos
            ))
        
        return result
    
    @staticmethod
    def _build_conteo_response(db: Session, conteo: Conteo) -> ConteoResponse:
        """Construir respuesta completa del conteo con detalles"""
        
        # Hacer join con Catalogo para obtener el nombre del producto
        detalles_query = db.query(
            ConteoDetalles,
            Catalogo.Producto
        ).join(
            Catalogo,
            ConteoDetalles.CodigoBarras == Catalogo.CodigoBarras
        ).filter(
            ConteoDetalles.IdConteo == conteo.idConteo
        ).all()
        
        # Construir lista de detalles con el nombre del producto
        detalles = []
        for detalle, producto_nombre in detalles_query:
            detalle_dict = {
                "idConteoDetalles": detalle.idConteoDetalles,
                "IdConteo": detalle.IdConteo,
                "CodigoBarras": detalle.CodigoBarras,
                "NSistema": detalle.NSistema,
                "NExcistencia": detalle.NExcistencia,
                "Precio": detalle.Precio,
                "Producto": producto_nombre
            }
            detalles.append(detalle_dict)
        
        return ConteoResponse(
            idConteo=conteo.idConteo,
            Fechal=conteo.Fechal,
            Envio=conteo.Envio,
            IdRealizo=conteo.IdRealizo,
            IdCentro=conteo.IdCentro,
            IdUsuario=conteo.IdUsuario,
            detalles=detalles
        )
