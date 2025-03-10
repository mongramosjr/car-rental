from django.contrib import admin
from .models import Booking, BookingStatusLog


class BookingStatusLogInline(admin.TabularInline):
    model = BookingStatusLog
    extra = 0  # Don't show any extra empty forms


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle', 'start_time', 'end_time', 'total_price', 'status')
    list_filter = ('status',)
    search_fields = ('user__first_name', 'user__last_name')
    inlines = [BookingStatusLogInline]  # Assuming you've created an inline for BookingStatusLog



