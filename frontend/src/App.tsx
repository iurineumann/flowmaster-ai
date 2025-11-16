// frontend/src/App.tsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';
// ✅ CORREÇÃO 1: Importa os tipos (type) para o Drag-and-Drop
import { 
  DragDropContext, 
  Droppable, 
  Draggable, 
  type DropResult, 
  type DroppableProvided, 
  type DraggableProvided, 
  type DraggableStateSnapshot 
} from '@hello-pangea/dnd';
import Login from './Login';
import { apiService } from './services/apiClient';
import type { ActiveModuleConfig, UserModulePreference } from './types/models';

// Componentes
import ContextCard from './agents/ContextCard';
import SkillCard from './agents/SkillCard';
import ReserveCard from './agents/ReserveCard';
import ChatWidget from './components/ChatWidget';

// UI
// ✅ CORREÇÃO 2: Remove 'Save' (não utilizado)
import { LayoutDashboard, LogOut, Bell } from 'lucide-react';

// Mapa de Componentes
const COMPONENT_MAP: Record<string, React.FC<any>> = {
  'context_agent': ContextCard,
  'skill_agent': SkillCard,
  'reserve_agent': ReserveCard,
  'meeting_agent': ContextCard, // Fallback temporário
};

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!localStorage.getItem('jwt_token'));
  const [activeModules, setActiveModules] = useState<ActiveModuleConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    if (!isAuthenticated) return;

    const initDashboard = async () => {
      setLoading(true);
      try {
        const [systemModules, userConfig] = await Promise.all([
            apiService.getSystemModules(),
            apiService.getUserConfig()
        ]);

        setTheme(userConfig.theme);

        const modules = userConfig.modules
          .filter(pref => pref.is_active)
          .map(pref => {
            const details = systemModules.find(sys => sys.id === pref.module_id);
            return details ? { ...details, ...pref } : null;
          })
          .filter(Boolean) as ActiveModuleConfig[];

        modules.sort((a, b) => a.display_order - b.display_order);
        setActiveModules(modules);

      } catch (error) {
        console.error("Erro ao carregar dashboard:", error);
        if (axios.isAxiosError(error) && error.response?.status === 401) {
            setIsAuthenticated(false);
        }
      } finally {
        setLoading(false);
      }
    };

    initDashboard();
  }, [isAuthenticated]);

  const handleOnDragEnd = async (result: DropResult) => {
    if (!result.destination) return;

    const items = Array.from(activeModules);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    const updatedItems = items.map((item, index) => ({
        ...item,
        display_order: index + 1
    }));
    setActiveModules(updatedItems);

    const preferences: UserModulePreference[] = updatedItems.map(m => ({
        module_id: m.id, 
        is_active: m.is_active,
        display_order: m.display_order
    }));

    try {
        await apiService.updateUserModules(preferences);
    } catch (e) {
        console.error("Falha ao salvar ordem", e);
    }
  };

  if (!isAuthenticated) return <Login onLoginSuccess={() => setIsAuthenticated(true)} />;
  
  if (loading) {
    return (
        <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
    );
  }

  return (
    <div className={`min-h-screen bg-gray-50 text-foreground ${theme === 'dark' ? 'dark bg-gray-950' : ''}`}>
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 py-4 flex justify-between items-center sticky top-0 z-10 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="bg-primary/10 p-2 rounded-lg">
            <LayoutDashboard className="w-6 h-6 text-primary" />
          </div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">FlowMaster AI</h1>
        </div>
        <div className="flex items-center gap-4">
            <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-full relative">
                <Bell className="w-5 h-5" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>
            <div className="h-6 w-px bg-gray-200"></div>
            <button onClick={() => { localStorage.removeItem('jwt_token'); setIsAuthenticated(false); }} className="text-sm font-medium hover:text-primary flex items-center gap-2">
                <LogOut className="w-4 h-4" /> Sair
            </button>
        </div>
      </header>

      <main className="p-6 max-w-[1600px] mx-auto">
        <DragDropContext onDragEnd={handleOnDragEnd}>
          <Droppable droppableId="dashboard-modules" direction="horizontal">
            {/* ✅ CORREÇÃO 3: Tipagem explícita de 'provided' */}
            {(provided: DroppableProvided) => (
              <div 
                {...provided.droppableProps} 
                ref={provided.innerRef}
                className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6"
              >
                {activeModules.map((module, index) => {
                  const AgentComponent = COMPONENT_MAP[module.id];
                  if (!AgentComponent) return null;

                  return (
                    <Draggable key={module.id} draggableId={module.id} index={index}>
                      {/* ✅ CORREÇÃO 4: Tipagem explícita de 'provided' e 'snapshot' */}
                      {(provided: DraggableProvided, snapshot: DraggableStateSnapshot) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          style={{ 
                            ...provided.draggableProps.style,
                            gridColumn: `span ${module.grid_column_span}` 
                          }}
                          className={`${snapshot.isDragging ? 'z-50 opacity-90 scale-105' : ''} transition-all duration-200`}
                        >
                          <div className="h-full">
                            <AgentComponent 
                              apiEndpoint={`/api${module.api_endpoint}`} 
                              title={module.name}
                            />
                          </div>
                        </div>
                      )}
                    </Draggable>
                  );
                })}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>
      </main>
      
      <ChatWidget />
    </div>
  );
}

export default App;