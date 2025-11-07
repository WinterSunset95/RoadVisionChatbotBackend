"""
Service for performing actions on tenders.
"""
import uuid
import os
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.modules.tenderiq.db.tenderiq_repository import TenderIQRepository
from app.modules.tenderiq.db.repository import TenderRepository, TenderWishlistRepository
from app.modules.tenderiq.models.pydantic_models import (
    TenderActionRequest, 
    TenderActionType,
    HistoryWishlistResponseSchema,
    TenderWishlistItemSchema
)
from app.modules.tenderiq.db.schema import Tender, TenderActionEnum

class TenderActionService:
    def __init__(self, db: Session):
        self.db = db
        self.tender_repo = TenderRepository(db)
        self.scraped_tender_repo = TenderIQRepository(db)
        self.wishlist_repo = TenderWishlistRepository(db)

    def perform_action(self, tender_id: uuid.UUID, user_id: uuid.UUID, request: TenderActionRequest) -> Tender:
        scraped_tender = self.scraped_tender_repo.get_tender_by_id(tender_id)
        if not scraped_tender:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

        tender = self.tender_repo.get_or_create_by_id(scraped_tender)

        updates = {}
        action_to_log: Optional[TenderActionEnum] = None
        notes = request.payload.notes if request.payload else None

        if request.action == TenderActionType.TOGGLE_WISHLIST:
            updates['is_wishlisted'] = not tender.is_wishlisted
            action_to_log = TenderActionEnum.wishlisted if updates['is_wishlisted'] else TenderActionEnum.unwishlisted
        elif request.action == TenderActionType.TOGGLE_FAVORITE:
            updates['is_favorite'] = not tender.is_favorite

        elif request.action == TenderActionType.TOGGLE_ARCHIVE:
            updates['is_archived'] = not tender.is_archived

        elif request.action == TenderActionType.UPDATE_STATUS:
            if not request.payload or not request.payload.status:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status payload is required for this action")
            updates['status'] = request.payload.status.value
            if request.payload.status.value == "Shortlisted":
                action_to_log = TenderActionEnum.shortlisted
        elif request.action == TenderActionType.UPDATE_REVIEW_STATUS:
            if not request.payload or not request.payload.review_status:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review status payload is required for this action")
            updates['review_status'] = request.payload.review_status.value
            if request.payload.review_status.value == "Shortlisted" and tender.status != "Shortlisted":
                action_to_log = TenderActionEnum.shortlisted

        if updates:
            updated_tender = self.tender_repo.update(tender, updates)
        else:
            updated_tender = tender

        if action_to_log:
            self.tender_repo.log_action(tender_id, user_id, action_to_log, notes)
        return updated_tender

    # ==================== NEW: WISHLIST METHODS ====================

    def get_comprehensive_report_url(self) -> str:
        """
        Generate URL for comprehensive report Excel export.
        
        Returns:
            URL string pointing to the report download endpoint
        """
        api_root = os.getenv('API_ROOT', 'http://localhost:8000')
        return f"{api_root}/api/tenderiq/download/comprehensive-report"

    def get_history_wishlist(self) -> HistoryWishlistResponseSchema:
        """
        Retrieve all tenders from wishlist/history with report URL.
        
        Workflow:
        1. Fetch all wishlist tenders from repository
        2. Convert ORM models to Pydantic schemas
        3. Generate comprehensive report URL
        4. Return combined response
        
        Returns:
            HistoryWishlistResponseSchema with report URL and tenders list
            
        Raises:
            HTTPException: If database query fails
        """
        try:
            # Get all tenders from wishlist, ordered by latest added first
            wishlist_tenders = self.wishlist_repo.get_all_wishlist_tenders()
            
            # Convert ORM models to Pydantic response schemas
            tender_items = [
                TenderWishlistItemSchema(**tender.to_dict())
                for tender in wishlist_tenders
            ]
            
            # Get report download URL
            report_url = self.get_comprehensive_report_url()
            
            # Return complete response matching endpoint specification
            return HistoryWishlistResponseSchema(
                report_file_url=report_url,
                tenders=tender_items
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve wishlist history: {str(e)}"
            )

    def get_user_wishlist(self, user_id: uuid.UUID) -> HistoryWishlistResponseSchema:
        """
        Retrieve wishlist tenders for a specific user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            HistoryWishlistResponseSchema with user's saved tenders
        """
        try:
            wishlist_tenders = self.wishlist_repo.get_user_wishlist(user_id)
            tender_items = [
                TenderWishlistItemSchema(**tender.to_dict())
                for tender in wishlist_tenders
            ]
            
            return HistoryWishlistResponseSchema(
                report_file_url=self.get_comprehensive_report_url(),
                tenders=tender_items
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve user wishlist: {str(e)}"
            )

    def add_tender_to_wishlist(self, tender_data: dict) -> TenderWishlistItemSchema:
        """
        Add a tender to user's wishlist.
        
        Args:
            tender_data: Dictionary containing tender information
            
        Returns:
            TenderWishlistItemSchema of the newly added tender
        """
        try:
            wishlist_entry = self.wishlist_repo.add_to_wishlist(tender_data)
            return TenderWishlistItemSchema(**wishlist_entry.to_dict())
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add tender to wishlist: {str(e)}"
            )

    def remove_tender_from_wishlist(self, wishlist_id: str) -> bool:
        """
        Remove a tender from user's wishlist.
        
        Args:
            wishlist_id: ID of wishlist entry to remove
            
        Returns:
            True if successfully removed
        """
        try:
            return self.wishlist_repo.remove_from_wishlist(wishlist_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove tender from wishlist: {str(e)}"
            )

    def update_wishlist_progress(self, wishlist_id: str, **kwargs) -> TenderWishlistItemSchema:
        """
        Update progress/status fields for a wishlist tender.
        
        Supports updating:
        - progress (0-100%)
        - analysis_state (bool)
        - synopsis_state (bool)
        - evaluated_state (bool)
        - results (won/rejected/incomplete/pending)
        - status_message (str)
        - error_message (str)
        
        Args:
            wishlist_id: ID of wishlist entry to update
            **kwargs: Fields to update
            
        Returns:
            TenderWishlistItemSchema of the updated tender
        """
        try:
            updated_tender = self.wishlist_repo.update_wishlist_progress(wishlist_id, **kwargs)
            if not updated_tender:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Wishlist entry not found"
                )
            return TenderWishlistItemSchema(**updated_tender.to_dict())
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update wishlist progress: {str(e)}"
            )

    def get_wishlist_by_status(self, status: str) -> HistoryWishlistResponseSchema:
        """
        Get all wishlist tenders with a specific status.
        
        Args:
            status: Status value (won/rejected/incomplete/pending)
            
        Returns:
            HistoryWishlistResponseSchema with filtered tenders
        """
        try:
            wishlist_tenders = self.wishlist_repo.get_wishlist_by_status(status)
            tender_items = [
                TenderWishlistItemSchema(**tender.to_dict())
                for tender in wishlist_tenders
            ]
            
            return HistoryWishlistResponseSchema(
                report_file_url=self.get_comprehensive_report_url(),
                tenders=tender_items
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve wishlist by status: {str(e)}"
            )
