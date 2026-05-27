import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Calendar, Clock, Check, X } from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import '../../styles/VendorAvailabilityCalendar.css';

const VendorAvailabilityCalendar = ({ vendorId, onDateSelect, readOnly = false }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [availability, setAvailability] = useState({});
  const [selectedDates, setSelectedDates] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [timeSlots, setTimeSlots] = useState([]);
  const [selectedTimeSlot, setSelectedTimeSlot] = useState(null);

  const timeSlotOptions = [
    { id: '09:00', label: '9:00 AM - 12:00 PM' },
    { id: '12:00', label: '12:00 PM - 3:00 PM' },
    { id: '15:00', label: '3:00 PM - 6:00 PM' },
    { id: '18:00', label: '6:00 PM - 9:00 PM' },
  ];

  useEffect(() => {
    if (vendorId && !readOnly) {
      loadAvailability();
    }
  }, [vendorId, readOnly]);

  const loadAvailability = async () => {
    setLoading(true);
    try {
      // In production, this would call: GET /api/vendors/{vendorId}/availability
      // For now, load from localStorage or API
      const storedAvailability = localStorage.getItem(`vendor_availability_${vendorId}`);
      if (storedAvailability) {
        setAvailability(JSON.parse(storedAvailability));
      }
    } catch (error) {
      console.error('Failed to load availability:', error);
    } finally {
      setLoading(false);
    }
  };

  const daysInMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const firstDayOfMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const handlePreviousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1));
  };

  const handleDateClick = (day) => {
    if (readOnly) return;

    const selectedDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
    const dateKey = selectedDate.toISOString().split('T')[0];

    const newSelectedDates = new Set(selectedDates);
    if (newSelectedDates.has(dateKey)) {
      newSelectedDates.delete(dateKey);
    } else {
      newSelectedDates.add(dateKey);
    }
    setSelectedDates(newSelectedDates);

    // Set time slots for this date if defined
    if (availability[dateKey]) {
      setTimeSlots(availability[dateKey].slots || timeSlotOptions);
    } else {
      setTimeSlots(timeSlotOptions);
    }

    if (onDateSelect) {
      onDateSelect({
        date: dateKey,
        timeSlot: selectedTimeSlot,
      });
    }
  };

  const handleTimeSlotChange = (slotId) => {
    setSelectedTimeSlot(slotId);
    if (onDateSelect && selectedDates.size > 0) {
      const lastSelectedDate = Array.from(selectedDates).pop();
      onDateSelect({
        date: lastSelectedDate,
        timeSlot: slotId,
      });
    }
  };

  const saveAvailability = async () => {
    setLoading(true);
    try {
      const availabilityData = {};
      selectedDates.forEach(date => {
        availabilityData[date] = {
          available: true,
          slots: timeSlots,
          selectedSlot: selectedTimeSlot,
        };
      });

      // In production, this would POST to: /api/vendors/{vendorId}/availability
      localStorage.setItem(`vendor_availability_${vendorId}`, JSON.stringify(availabilityData));
      setAvailability(availabilityData);
      alert('Availability saved successfully!');
      setSelectedDates(new Set());
      setSelectedTimeSlot(null);
    } catch (error) {
      console.error('Failed to save availability:', error);
      alert('Failed to save availability');
    } finally {
      setLoading(false);
    }
  };

  const isDateAvailable = (day) => {
    const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
    const dateKey = date.toISOString().split('T')[0];
    return availability[dateKey]?.available || false;
  };

  const isDateSelected = (day) => {
    const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
    const dateKey = date.toISOString().split('T')[0];
    return selectedDates.has(dateKey);
  };

  const isDateInPast = (day) => {
    const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
    return date < new Date();
  };

  const renderCalendarDays = () => {
    const days = [];
    const totalDays = daysInMonth(currentDate);
    const firstDay = firstDayOfMonth(currentDate);

    // Empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="vendor-availability-empty-day"></div>);
    }

    // Days of month
    for (let day = 1; day <= totalDays; day++) {
      const available = isDateAvailable(day);
      const selected = isDateSelected(day);
      const isPast = isDateInPast(day);

      days.push(
        <button
          key={day}
          onClick={() => handleDateClick(day)}
          disabled={isPast || readOnly}
          className={`vendor-availability-day ${
            selected ? 'selected' : available ? 'available' : ''
          } ${isPast ? 'past' : ''} ${readOnly ? 'read-only' : ''}`}
          title={available ? 'Available' : 'Not available'}
        >
          <span className="vendor-availability-day-number">{day}</span>
          {available && !selected && (
            <Check className="vendor-availability-day-icon" size={14} />
          )}
          {selected && (
            <span className="vendor-availability-day-badge">✓</span>
          )}
        </button>
      );
    }

    return days;
  };

  const monthYear = currentDate.toLocaleString('en-US', { month: 'long', year: 'numeric' });

  return (
    <Card className="vendor-availability-card bg-white border-stone-200 p-6 rounded-2xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="text-primary" size={24} />
            <h3 className="text-xl font-bold text-stone-900">
              {readOnly ? 'Availability' : 'Manage Availability'}
            </h3>
          </div>
        </div>

        {/* Calendar Navigation */}
        <div className="flex items-center justify-between p-4 bg-stone-50 rounded-lg">
          <button
            onClick={handlePreviousMonth}
            disabled={readOnly}
            className="p-2 hover:bg-white rounded-lg transition-colors"
          >
            <ChevronLeft size={20} className="text-stone-600" />
          </button>
          <h4 className="font-semibold text-stone-900 text-center flex-1">{monthYear}</h4>
          <button
            onClick={handleNextMonth}
            disabled={readOnly}
            className="p-2 hover:bg-white rounded-lg transition-colors"
          >
            <ChevronRight size={20} className="text-stone-600" />
          </button>
        </div>

        {/* Calendar Grid */}
        <div className="vendor-availability-calendar">
          {/* Day headers */}
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
            <div key={`header-${day}`} className="vendor-availability-day-header">
              {day}
            </div>
          ))}

          {/* Days */}
          {renderCalendarDays()}
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 text-xs pt-4 border-t border-stone-200">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-primary/20 border border-primary"></div>
            <span className="text-stone-600">Selected</span>
          </div>
          <div className="flex items-center gap-2">
            <Check size={14} className="text-green-600" />
            <span className="text-stone-600">Available</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-stone-200"></div>
            <span className="text-stone-600">Unavailable</span>
          </div>
        </div>

        {/* Time Slot Selection */}
        {selectedDates.size > 0 && !readOnly && (
          <div className="space-y-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center gap-2 mb-3">
              <Clock className="text-blue-600" size={18} />
              <label className="font-semibold text-stone-900">
                Select Time Slots for {selectedDates.size} selected date(s)
              </label>
            </div>
            <div className="space-y-2">
              {timeSlotOptions.map((slot) => (
                <label key={slot.id} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="timeSlot"
                    value={slot.id}
                    checked={selectedTimeSlot === slot.id}
                    onChange={() => handleTimeSlotChange(slot.id)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-stone-700">{slot.label}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        {!readOnly && selectedDates.size > 0 && (
          <div className="flex gap-3 pt-4">
            <Button
              onClick={saveAvailability}
              disabled={loading || !selectedTimeSlot}
              className="flex-1 bg-primary hover:bg-primary/90 text-white font-semibold rounded-lg"
            >
              {loading ? 'Saving...' : `Save ${selectedDates.size} Dates`}
            </Button>
            <Button
              onClick={() => {
                setSelectedDates(new Set());
                setSelectedTimeSlot(null);
              }}
              variant="outline"
              className="border-stone-300 text-stone-700 font-semibold rounded-lg"
            >
              Clear Selection
            </Button>
          </div>
        )}

        {/* Info Text */}
        <p className="text-xs text-stone-500">
          {readOnly
            ? 'Showing vendor availability for booking'
            : 'Select dates when you are available to take bookings. Add time slots for each availability window.'}
        </p>
      </div>
    </Card>
  );
};

export default VendorAvailabilityCalendar;
