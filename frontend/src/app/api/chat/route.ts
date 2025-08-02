// Enhanced appointment booking chatbot
export const maxDuration = 30;

// Session storage for conversation state (in production, use a proper session store)
const conversationState = new Map();

export async function POST(req: Request) {
  const { messages } = await req.json();
  
  const sessionId = 'default'; // In production, generate unique session IDs
  const lastMessage = messages[messages.length - 1]?.content?.toLowerCase() || '';
  
  // Get or initialize conversation state
  let state = conversationState.get(sessionId) || {
    step: 0,
    data: {}
  };
  
  let response = '';
  
  // Check if user wants to start over
  if (lastMessage.includes('book an appointment') || lastMessage.includes('start over')) {
    state = { step: 1, data: {} };
    response = `I'd be happy to help you book an appointment at NaviMed! 🏥

Let's start with your full name. What's your name?`;
  }
  // Step-by-step information collection
  else if (state.step === 1 && lastMessage.trim().length > 1) {
    // Collect name
    state.data.name = messages[messages.length - 1]?.content;
    state.step = 2;
    response = `Thank you, ${state.data.name}! 

What's your email address?`;
  }
  else if (state.step === 2 && (lastMessage.includes('@') || lastMessage.includes('.'))) {
    // Collect email
    state.data.email = messages[messages.length - 1]?.content;
    state.step = 3;
    response = `Perfect! 

What's your phone number?`;
  }
  else if (state.step === 3 && lastMessage.match(/[\d\-\(\)\+\s]{8,}/)) {
    // Collect phone
    state.data.phone = messages[messages.length - 1]?.content;
    state.step = 4;
    response = `Great! 

How old are you?`;
  }
  else if (state.step === 4 && lastMessage.match(/\d{1,3}/)) {
    // Collect age
    const age = parseInt(lastMessage.match(/\d{1,3}/)[0]);
    if (age > 0 && age < 120) {
      state.data.age = age;
      state.step = 5;
      response = `Thank you! 

What's your gender?
• male
• female  
• other`;
    } else {
      response = `Please enter a valid age (1-120 years).`;
    }
  }
  else if (state.step === 5 && lastMessage.match(/male|female|other/)) {
    // Collect gender
    state.data.gender = lastMessage.match(/male|female|other/)[0];
    state.step = 6;
    response = `Perfect! 

What type of appointment do you need?
• **consultation** - General medical consultation
• **checkup** - Routine health checkup
• **follow_up** - Follow-up visit
• **emergency** - Urgent medical care
• **specialist** - Specialist consultation

Just type one of the options above.`;
  }
  else if (state.step === 6 && lastMessage.match(/consultation|checkup|follow|emergency|specialist/)) {
    // Collect appointment type and directly book appointment
    let appointmentType = lastMessage.match(/consultation|checkup|follow|emergency|specialist/)[0];
    
    // Map to backend appointment types (lowercase as expected by backend)
    const typeMapping: Record<string, string> = {
      'consultation': 'consultation',
      'checkup': 'general_checkup', 
      'follow': 'follow_up',
      'emergency': 'emergency',
      'specialist': 'specialist'
    };
    
    state.data.appointmentType = typeMapping[appointmentType] || 'consultation';
    
    // Auto-select urgency and book immediately
    const isEmergency = appointmentType === 'emergency';
    
    // Book the appointment directly
    try {
      console.log('Booking appointment with data:', state.data);
      
      const bookingResponse = await fetch('http://localhost:8000/book_appointment_rl', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patient_name: state.data.name,
          patient_email: state.data.email,
          patient_phone: state.data.phone,
          age: parseInt(state.data.age),
          gender: state.data.gender,
          appointment_type: state.data.appointmentType,
          symptoms: `${appointmentType} appointment requested`,
          is_emergency: isEmergency
        }),
      });

      console.log('Booking response status:', bookingResponse.status);
      const responseText = await bookingResponse.text();
      console.log('Booking response body:', responseText);

      if (bookingResponse.ok) {
        let result;
        try {
          result = JSON.parse(responseText);
        } catch {
          result = { message: responseText };
        }
        
        response = `🎉 **Appointment Successfully Booked!**

📋 **Your Details:**
• **Name:** ${state.data.name}
• **Email:** ${state.data.email}
• **Phone:** ${state.data.phone}
• **Age:** ${state.data.age}
• **Gender:** ${state.data.gender}
• **Type:** ${appointmentType.replace('_', ' ')}
• **Appointment ID:** ${result.appointment_id || 'Generated'}
• **Queue Position:** #${result.queue_position || 'TBD'}
• **Estimated Wait:** ${result.estimated_wait_minutes || 'TBD'} minutes

📧 You should receive a confirmation email shortly with all the details.

Thank you for choosing NaviMed! 🏥`;
        
        // Reset conversation
        state = { step: 0, data: {} };
      } else {
        console.error('Booking failed:', responseText);
        response = `❌ Sorry, there was an error booking your appointment: ${responseText}

Would you like to try booking again?`;
        state.step = 0;
      }
    } catch (error) {
      console.error('Network error:', error);
      response = `❌ Sorry, there was a connection error. Please make sure the backend server is running on http://localhost:8000

Would you like to try booking again?`;
      state.step = 0;
    }
  }
  else if (state.step === 7 && lastMessage.match(/routine|urgent|emergency/)) {
    // This step is now removed - keeping for backward compatibility
    response = `This step has been simplified. Please start over by saying "book an appointment".`;
    state.step = 0;
  }
  else if (state.step === 8 && lastMessage.trim().length > 5) {
    // This step is now removed - booking happens directly after appointment type selection
    response = `Appointment booking has been simplified. Please start over by saying "book an appointment".`;
    state.step = 0;
  }
  // Handle invalid inputs for each step
  else {
    switch (state.step) {
      case 1:
        response = `Please enter your full name to continue.`;
        break;
      case 2:
        response = `Please enter a valid email address (example: name@email.com).`;
        break;
      case 3:
        response = `Please enter a valid phone number.`;
        break;
      case 4:
        response = `Please enter your age as a number.`;
        break;
      case 5:
        response = `Please choose: male, female, or other.`;
        break;
      case 6:
        response = `Please choose one: consultation, checkup, follow, emergency, or specialist.`;
        break;
      case 7:
        response = `This step has been removed. Please start over by saying "book an appointment".`;
        break;
      case 8:
        response = `This step has been removed. Please start over by saying "book an appointment".`;
        break;
      default:
        response = `Hi! I'm your NaviMed assistant. 😊

I can help you book a medical appointment. Just say "I'd like to book an appointment" to get started!`;
        state.step = 0;
    }
  }
  
  // Save conversation state
  conversationState.set(sessionId, state);

  // Return response as text stream
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(response));
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/plain',
      'Cache-Control': 'no-cache',
    },
  });
}
