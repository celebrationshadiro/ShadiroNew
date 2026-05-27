import React, { useState, useEffect } from 'react';
import { Calendar, MapPin, Users, Music, Utensils, Camera, Zap, Check, Clock, AlertCircle } from 'lucide-react';
import { Card } from './ui/card';
import '../../styles/EventTimeline.css';

const EventTimeline = ({ event, vendors = [] }) => {
  const [timeline, setTimeline] = useState([]);
  const [expandedPhase, setExpandedPhase] = useState(null);

  useEffect(() => {
    generateTimeline();
  }, [event, vendors]);

  const generateTimeline = () => {
    if (!event) return;

    const eventDate = new Date(event.date);
    const today = new Date();
    const daysUntilEvent = Math.ceil((eventDate - today) / (1000 * 60 * 60 * 24));

    const timelinePhases = [
      {
        id: 1,
        phase: 'Planning',
        duration: 'Now - 3 months before',
        daysUntilEvent: daysUntilEvent > 90 ? daysUntilEvent - 90 : 0,
        icon: <Zap size={24} className="text-purple-500" />,
        tasks: [
          { title: 'Define budget & guest list', completed: event.guest_count > 0 },
          { title: 'Choose event date & location', completed: !!event.location },
          { title: 'Browse vendor categories', completed: vendors.length > 0 },
          { title: 'Create vendor wishlist', completed: vendors.filter(v => v.saved).length > 0 },
        ],
      },
      {
        id: 2,
        phase: 'Vendor Selection',
        duration: '3 - 6 weeks before',
        daysUntilEvent: daysUntilEvent > 42 ? daysUntilEvent - 42 : 0,
        icon: <Camera size={24} className="text-blue-500" />,
        tasks: [
          { title: 'Compare vendor packages', completed: vendors.filter(v => v.compared).length > 0 },
          { title: 'Send quote requests', completed: vendors.filter(v => v.quoted).length > 0 },
          { title: 'Review quote responses', completed: vendors.filter(v => v.has_quote).length > 0 },
          { title: 'Finalize vendor selections', completed: vendors.filter(v => v.booked).length >= 3 },
        ],
      },
      {
        id: 3,
        phase: 'Logistics',
        duration: '6 weeks - 1 week before',
        daysUntilEvent: daysUntilEvent > 7 ? daysUntilEvent - 7 : 0,
        icon: <Utensils size={24} className="text-orange-500" />,
        tasks: [
          { title: 'Finalize menus & services', completed: false },
          { title: 'Confirm vendor timeline', completed: false },
          { title: 'Arrange transportation', completed: false },
          { title: 'Confirm guest attendance', completed: false },
        ],
      },
      {
        id: 4,
        phase: 'Final Preparations',
        duration: '1 week before',
        daysUntilEvent: daysUntilEvent <= 7 ? daysUntilEvent : 0,
        icon: <Clock size={24} className="text-amber-500" />,
        tasks: [
          { title: 'Final vendor confirmations', completed: false },
          { title: 'Prepare detailed timeline', completed: false },
          { title: 'Contact all vendors', completed: false },
          { title: 'Brief final details', completed: false },
        ],
      },
      {
        id: 5,
        phase: 'Event Day',
        duration: 'The big day!',
        daysUntilEvent: 0,
        icon: <Zap size={24} className="text-red-500" />,
        tasks: [
          { title: 'Arrive at venue early', completed: false },
          { title: 'Coordinate with vendors', completed: false },
          { title: 'Manage timeline', completed: false },
          { title: 'Capture moments', completed: false },
        ],
      },
    ];

    setTimeline(timelinePhases);
  };

  const getCurrentPhase = () => {
    if (!event) return null;
    const eventDate = new Date(event.date);
    const today = new Date();
    const daysUntilEvent = Math.ceil((eventDate - today) / (1000 * 60 * 60 * 24));

    if (daysUntilEvent > 90) return 1;
    if (daysUntilEvent > 42) return 2;
    if (daysUntilEvent > 7) return 3;
    if (daysUntilEvent >= 0) return 4;
    return 5;
  };

  const getPhaseProgress = (tasks) => {
    const completed = tasks.filter(t => t.completed).length;
    return Math.round((completed / tasks.length) * 100);
  };

  const currentPhase = getCurrentPhase();

  if (!event) {
    return (
      <Card className="bg-white border-stone-200 p-8 text-center">
        <p className="text-stone-600">No event selected</p>
      </Card>
    );
  }

  return (
    <div className="event-timeline-container space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary/10 to-pink-500/10 rounded-2xl p-8 border border-primary/20">
        <h2 className="text-3xl font-bold text-stone-900 mb-4">Event Planning Timeline</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div>
            <p className="text-sm text-stone-600 mb-1">Event Date</p>
            <p className="text-lg font-semibold text-stone-900">
              {new Date(event.date).toLocaleDateString('en-IN', { 
                weekday: 'short', 
                month: 'short', 
                day: 'numeric',
                year: 'numeric'
              })}
            </p>
          </div>
          <div>
            <p className="text-sm text-stone-600 mb-1">Location</p>
            <p className="text-lg font-semibold text-stone-900 flex items-center gap-2">
              <MapPin size={16} /> {event.location || 'TBD'}
            </p>
          </div>
          <div>
            <p className="text-sm text-stone-600 mb-1">Expected Guests</p>
            <p className="text-lg font-semibold text-stone-900 flex items-center gap-2">
              <Users size={16} /> {event.guest_count || '—'}
            </p>
          </div>
          <div>
            <p className="text-sm text-stone-600 mb-1">Budget</p>
            <p className="text-lg font-semibold text-stone-900">
              ₹{event.budget_max?.toLocaleString('en-IN') || '—'}
            </p>
          </div>
        </div>
      </div>

      {/* Timeline Phases */}
      <div className="space-y-4">
        {timeline.map((phase, index) => {
          const isCurrentPhase = phase.id === currentPhase;
          const isPastPhase = phase.id < currentPhase;
          const progress = getPhaseProgress(phase.tasks);

          return (
            <Card
              key={phase.id}
              className={`border-2 transition-all cursor-pointer ${
                isCurrentPhase
                  ? 'border-primary bg-primary/5 shadow-lg'
                  : isPastPhase
                  ? 'border-green-200 bg-green-50/50'
                  : 'border-stone-200 hover:border-primary/30'
              }`}
              onClick={() => setExpandedPhase(expandedPhase === phase.id ? null : phase.id)}
            >
              <div className="p-6">
                {/* Phase Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start gap-4 flex-1">
                    <div className="p-3 rounded-lg bg-stone-100">
                      {phase.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-xl font-bold text-stone-900">{phase.phase}</h3>
                        {isCurrentPhase && (
                          <span className="px-2 py-1 bg-primary text-white text-xs font-bold rounded-full">
                            CURRENT
                          </span>
                        )}
                        {isPastPhase && (
                          <span className="px-2 py-1 bg-green-500 text-white text-xs font-bold rounded-full">
                            COMPLETED
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-stone-600">{phase.duration}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-primary">{progress}%</p>
                    <p className="text-xs text-stone-600">Progress</p>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-stone-200 rounded-full h-2 mb-6 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      isPastPhase ? 'bg-green-500' : 'bg-primary'
                    }`}
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>

                {/* Tasks (Expandable) */}
                <div
                  className={`overflow-hidden transition-all duration-300 ${
                    expandedPhase === phase.id ? 'max-h-96' : 'max-h-0'
                  }`}
                >
                  <div className="space-y-2 pt-4 border-t border-stone-200">
                    {phase.tasks.map((task, taskIndex) => (
                      <div key={taskIndex} className="flex items-center gap-3">
                        <div
                          className={`flex-shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                            task.completed
                              ? 'bg-green-500 border-green-500'
                              : 'border-stone-300'
                          }`}
                        >
                          {task.completed && (
                            <Check size={14} className="text-white" />
                          )}
                        </div>
                        <span className={`text-sm ${task.completed ? 'text-green-700 line-through' : 'text-stone-700'}`}>
                          {task.title}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Expand Indicator */}
                <div className="text-center pt-2 text-xs text-stone-500">
                  {expandedPhase === phase.id ? '▲ Click to collapse' : '▼ Click to expand'}
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Tips Section */}
      <Card className="bg-blue-50 border-blue-200 p-6 rounded-2xl">
        <div className="flex items-start gap-3">
          <AlertCircle className="text-blue-600 flex-shrink-0 mt-1" size={20} />
          <div>
            <h4 className="font-semibold text-blue-900 mb-2">Planning Tips</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Start vendor search 3+ months before your event</li>
              <li>• Get quotes from at least 3 vendors in each category</li>
              <li>• Confirm all bookings at least 4 weeks before</li>
              <li>• Create detailed timeline 1 week before event</li>
              <li>• Do final check-ins with all vendors 2-3 days before</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default EventTimeline;
