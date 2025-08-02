"use client"
import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from '@/components/ui/separator';
import Link from "next/link";
import {
    Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectLabel,
    SelectTrigger,
    SelectValue,
  } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import axios from 'axios';

// Appointment type configuration with priorities
const APPOINTMENT_TYPES = [
  {
    value: 'general_checkup',
    label: 'General Checkup',
    priority: 'very_low',
    score: 1.0,
    color: '#8BC34A',
    description: 'Routine health checkup'
  },
  {
    value: 'followup',
    label: 'Follow up',
    priority: 'low',
    score: 2.0,
    color: '#4CAF50',
    description: 'Follow-up visit'
  },
  {
    value: 'diagnostics',
    label: 'Diagnostics',
    priority: 'medium',
    score: 3.5,
    color: '#FFC107',
    description: 'Diagnostic tests and procedures'
  },
  {
    value: 'consultation_routine',
    label: 'Consultation (Routine)',
    priority: 'high',
    score: 4.0,
    color: '#FF9800',
    description: 'Regular consultation'
  },
  {
    value: 'consultation_urgent',
    label: 'Consultation (Urgent)',
    priority: 'very_high',
    score: 5.0,
    color: '#F44336',
    description: 'Urgent medical attention needed'
  },
  {
    value: 'emergency',
    label: 'Emergency',
    priority: 'critical',
    score: 7.0,
    color: '#D32F2F',
    description: 'Emergency medical situation'
  }
];

// Function to get priority badge styling
const getPriorityBadgeStyle = (priority: string) => {
  const priorityStyles = {
    'very_low': 'bg-green-100 text-green-800 border-green-200',
    'low': 'bg-green-200 text-green-900 border-green-300',
    'medium': 'bg-yellow-100 text-yellow-800 border-yellow-200',
    'high': 'bg-orange-100 text-orange-800 border-orange-200',
    'very_high': 'bg-red-100 text-red-800 border-red-200',
    'critical': 'bg-red-200 text-red-900 border-red-300'
  };
  return priorityStyles[priority as keyof typeof priorityStyles] || priorityStyles.medium;
};

interface PatientBookingData {
  name: string;
  age: number;
  gender: string;
  appointment_type: string;
  priority: string;
  priority_score: number;
  is_emergency: boolean;
  symptoms?: string;
  phone: string;
  email: string;
}

export default function Appointment() {
  const [formData, setFormData] = useState<PatientBookingData>({
    name: '',
    age: 0,
    gender: '',
    appointment_type: '',
    priority: 'very_low',
    priority_score: 1.0,
    is_emergency: false,
    symptoms: '',
    phone: '',
    email: ''
  });

  const [loading, setLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submissionTime, setSubmissionTime] = useState<string>('');

  const handleInputChange = (field: keyof PatientBookingData, value: string | number | boolean) => {
    if (field === 'appointment_type' && typeof value === 'string') {
      const appointmentType = APPOINTMENT_TYPES.find(type => type.value === value);
      if (appointmentType) {
        setFormData(prev => ({
          ...prev,
          appointment_type: value,
          priority: appointmentType.priority,
          priority_score: appointmentType.score,
          is_emergency: value === 'emergency'
        }));
        return;
      }
    }
    if (field === 'is_emergency' && value === true) {
      const emergencyType = APPOINTMENT_TYPES.find(type => type.value === 'emergency');
      if (emergencyType) {
        setFormData(prev => ({
          ...prev,
          is_emergency: true,
          appointment_type: 'emergency',
          priority: emergencyType.priority,
          priority_score: emergencyType.score
        }));
        return;
      }
    }
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const validateRequiredFields = () => {
    const errors: string[] = [];

    if (!formData.name.trim()) {
      errors.push('Full Name is required');
    }

    if (!formData.age || formData.age < 1 || formData.age > 150) {
      errors.push('Please enter a valid age (1-150)');
    }

    if (!formData.email.trim()) {
      errors.push('Email is required');
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.push('Please enter a valid email address');
    }

    if (!formData.gender) {
      errors.push('Gender is required');
    }

    if (!formData.phone || formData.phone.length !== 10 || !/^\d{10}$/.test(formData.phone)) {
      errors.push('Please enter a valid 10-digit phone number');
    }

    if (!formData.appointment_type || formData.appointment_type === '') {
      errors.push('Please select an appointment type');
    }

    return errors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate required fields
    const validationErrors = validateRequiredFields();
    if (validationErrors.length > 0) {
      validationErrors.forEach(error => {
        toast.error(error);
      });
      return;
    }

    setLoading(true);

    try {
      // Submit to the RL-integrated booking endpoint
      const bookingData = {
        patient_name: formData.name,
        patient_email: formData.email,
        patient_phone: formData.phone,
        age: parseInt(formData.age.toString()),
        gender: formData.gender,
        date_of_birth: new Date().getFullYear() - formData.age + '-01-01',
        appointment_type: formData.appointment_type,
        symptoms: formData.symptoms || '',
        priority: formData.priority,
        priority_score: formData.priority_score,
        is_emergency: formData.is_emergency || false,
        preferred_doctor_id: null,
        notes: formData.symptoms || ''
      };

      console.log('Sending booking data:', bookingData);
      
      const response = await axios.post('http://localhost:8000/book_appointment_rl', bookingData);

      // Set success state and time
      const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      setSubmissionTime(currentTime);
      setIsSubmitted(true);

      toast.success(`Appointment booked successfully! Queue position: ${response.data.queue_position}, Estimated wait: ${response.data.estimated_wait_minutes} minutes`);

    } catch (error: unknown) {
      console.error('Booking error:', error);
      
      let errorMessage = 'Something went wrong';
      
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: unknown } } };
        console.error('Error response:', axiosError.response?.data);
        
        if (axiosError.response?.data?.detail) {
          const detail = axiosError.response.data.detail;
          
          // Handle validation errors (array format)
          if (Array.isArray(detail)) {
            errorMessage = detail.map((err: { loc?: string[]; msg?: string }) => 
              `${err.loc?.join(' → ') || 'Field'}: ${err.msg || 'Invalid value'}`
            ).join('; ');
          } 
          // Handle string error messages
          else if (typeof detail === 'string') {
            errorMessage = detail;
          }
          // Handle object with message
          else if (detail && typeof detail === 'object' && 'message' in detail) {
            errorMessage = (detail as { message: string }).message;
          }
        }
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="min-h-screen flex md:flex-row flex-col">
        <div className="md:w-1/2 bg-[#EFEDE8] pl-[5%] pt-12 relative">
            <div className="flex flex-col justify-start z-50">
                <Link href={'/'}>
                    <div className=" flex items-center gap-2">
                        <ChevronLeft className="md:w-8 md:h-8 w-4 h-4" />
                        <span className="text-black font-bold md:text-[28px] text-[18px] font-satoshi">NaviMed</span>
                    </div>
                </Link>
            </div>
              <div className='flex justify-center items-center h-screen absolute top-0 z-10 pointer-events-none'>
               <img src={'/cube.png'} alt='cube' className='h-[400px] w-auto ' />
             </div>
        </div>
            <div className="md:w-1/2 pr-[15%] pl-[5%] flex flex-col justify-center">
              <div>
                {isSubmitted ? (
                  <div className="flex flex-col items-center justify-center h-full text-center">
                    <div className="p-8 rounded-lg bg-green-50 border border-green-200">
                      <div className="text-green-600 text-2xl font-semibold mb-2">
                        ✓ Email sent with slot timings
                      </div>
                      <div className="text-green-700 text-sm">
                        Sent at {submissionTime}
                      </div>
                      <Button 
                        onClick={() => {
                          setIsSubmitted(false);
                          setFormData({
                            name: '',
                            age: 0,
                            gender: '',
                            appointment_type: '',
                            priority: 'very_low',
                            priority_score: 1.0,
                            is_emergency: false,
                            symptoms: '',
                            phone: '',
                            email: ''
                          });
                        }}
                        className="mt-4 cursor-pointer"
                        variant="outline"
                      >
                        Book Another Appointment
                      </Button>
                    </div>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className="flex flex-col space-y-6 h-full">
                      <div className="flex items-center gap-4">
                          <div className="flex flex-col gap-2 w-4/5">
                              <Label htmlFor="name" className='text-[12px]'>Full Name *</Label>
                              <Input
                                  id="name"
                                  type="text"
                                  placeholder="Enter your full name"
                                  className='text-[12px]'
                                  value={formData.name}
                                  onChange={(e) => handleInputChange('name', e.target.value)}
                                  required
                              />
                          </div>
                          <div className="flex flex-col gap-2 w-1/5">
                              <Label htmlFor="age" className='text-[12px]'>Age *</Label>
                              <Input
                                  id="age"
                                  type="number"
                                  placeholder="25"
                                  value={formData.age || ''}
                                  onChange={(e) => handleInputChange('age', parseInt(e.target.value) || 0)}
                                  min={1}
                                  max={150}
                                  required
                              />
                          </div>
                      </div>
                      <div className="flex flex-col gap-2">
                          <Label htmlFor="email" className='text-[12px]'>Email *</Label>
                          <Input
                              id="email"
                              type="email"
                              placeholder="your.email@example.com"
                              value={formData.email}
                              onChange={(e) => handleInputChange('email', e.target.value)}
                          />
                      </div>
                      <div className="flex items-center gap-4">
                          <div className="flex flex-col gap-2 w-1/2">
                              <Label className='text-[12px]' htmlFor="gender">Gender *</Label>
                              <Select value={formData.gender} onValueChange={(value) => handleInputChange('gender', value)}>
                                  <SelectTrigger className="w-full">
                                      <SelectValue placeholder="Select gender" />
                                  </SelectTrigger>
                                  <SelectContent>
                                      <SelectGroup>
                                          <SelectLabel>Gender</SelectLabel>
                                          <SelectItem value="male">Male</SelectItem>
                                          <SelectItem value="female">Female</SelectItem>
                                          <SelectItem value="other">Other</SelectItem>
                                      </SelectGroup>
                                  </SelectContent>
                              </Select>
                          </div>
                          <div className="flex flex-col gap-2 w-1/2">
                              <Label className='text-[12px]' htmlFor="phone">Phone Number *</Label>
                              <Input
                                  id="phone"
                                  type="tel"
                                  placeholder="1234567890"
                                  value={formData.phone}
                                  onChange={(e) => {
                                      // Allow only digits and limit to 10 characters
                                      const value = e.target.value.replace(/\D/g, '');
                                      if (value.length <= 10) {
                                          handleInputChange('phone', value);
                                      }
                                  }}
                                  maxLength={10}
                                  pattern="[0-9]*"
                                  required
                              />
                          </div>
                      </div>
                      <Separator className="my-4" />
                      <div className="flex flex-col gap-2 mt-4">
                          <Label className='text-[12px]' htmlFor="appointment_type">Appointment Type *</Label>
                          <Select value={formData.appointment_type || undefined} onValueChange={(value) => handleInputChange('appointment_type', value)}>
                                  <SelectTrigger className="w-full">
                                      <SelectValue placeholder="Select Appointment type" />
                                  </SelectTrigger>
                                  <SelectContent>
                                      <SelectGroup> 
                                          {APPOINTMENT_TYPES.map((type) => (
                                              <SelectItem key={type.value} value={type.value} className='w-full '>
                                                <div className='md:w-[30vw] w-[80vw] flex justify-content relative'>
                                                    <div className=''>
                                                      <span>{type.label}</span>
                                                    </div>
                                                    <div className='absolute right-0'>
                                                      <Badge 
                                                          variant="outline" 
                                                          className={getPriorityBadgeStyle(type.priority)}
                                                      >
                                                          {type.priority.replace('_', ' ').toUpperCase()}
                                                      </Badge>
                                                    </div>
                                                </div>
                                              </SelectItem>
                                          ))}
                                      </SelectGroup>
                                  </SelectContent>
                              </Select>
                              {/* {formData.appointment_type && (
                                  <span className="text-sm text-gray-500">
                                      Priority: {formData.priority.toUpperCase()} (Score: {formData.priority_score})
                                  </span>
                              )} */}
                      </div>
                      <div className="flex items-center gap-3">
                          <Checkbox 
                              id="emergency" 
                              checked={formData.is_emergency}
                              onCheckedChange={(checked) => handleInputChange('is_emergency', checked)}
                              disabled={formData.appointment_type === 'emergency'}
                          />
                          <Label htmlFor="emergency">
                              Emergency Case 
                              {formData.is_emergency && (
                                  <span className="ml-2 text-red-600 font-medium">🚨 PRIORITY</span>
                              )}
                          </Label>
                      </div>
                      <div className="flex flex-col gap-2 mt-2">
                          <Label className='text-[12px]' htmlFor="symptoms">Symptoms (Optional)</Label>
                          <Textarea
                              id="symptoms"
                              placeholder="Describe your symptoms briefly..."
                              value={formData.symptoms}
                              onChange={(e) => handleInputChange('symptoms', e.target.value)}
                              rows={5}
                          />
                      </div>
                      <Button type="submit" className="w-full mt-2" disabled={loading}>
                          {loading ? 'Booking...' : 'Book an Appointment'}
                      </Button>
                  </form>
                )}
              </div>
            </div>
    </div>
  )
}
