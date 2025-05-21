# PartSelect Agent Client

A clean, modern React+TypeScript UI for interacting with the PartSelect Agent API.

## Features

- Real-time communication with the agent via WebSocket
- Clean, responsive UI designed for desktop and mobile
- Markdown rendering for agent responses
- JSON response formatting for part information
- Quick action buttons for suggested responses
- Connection status indicator

## Installation

1. Navigate to the client directory:
```
cd src/client
```

2. Install dependencies:
```
npm install
```

## Running the Application

1. Make sure the server is running on port 9000

2. Start the development server:
```
npm start
```

This will start the client application on port 9001. Open your browser to [http://localhost:9001](http://localhost:9001) to use the application.

## Development

### Project Structure

- `src/App.tsx` - Main application component with WebSocket handling
- `src/components/ChatWindow.tsx` - Chat display component
- `src/components/QuickActions.tsx` - Quick action buttons component

### Building for Production

To create a production build:

```
npm run build
```

This will create a `build` directory with optimized production files.

## Technologies Used

- React 18
- TypeScript
- WebSocket API
- CSS3 with modern features 