// frontend/src/pages/DashboardPage.tsx

import React, { useState, useEffect } from 'react';
import { 
  DragDropContext, 
  Droppable, 
  Draggable, 
  type DropResult, 
  type DroppableProvided, 
  type DraggableProvided, 
  type DraggableStateSnapshot 
} from '@hello-pangea/dnd';
import { apiService } from '../services/apiClient';
import type { ActiveModuleConfig, UserModulePreference } from '../types/models';

// Componentes
import ContextCard from '../agents/ContextCard';
import SkillCard from '../agents/SkillCard';
import ReserveCard from '../agents/ReserveCard';
import MeetingCard from '../agents/MeetingCard'; // ✅ NOVO
import AdoAgentCard from '../agents/AdoAgentCard';

// Mapeamento Exato (IDs devem bater com initial_data_mock.py)
const COMPONENT_MAP: Record<string, React.FC<any>> = {
  'context_agent': ContextCard,
  'skill_agent': SkillCard,
  'reserve_agent': ReserveCard,
  'meeting_agent': MeetingCard,
  'ado_agent': AdoAgentCard,   
};

const DashboardPage: React.FC = () => {
  const [activeModules, setActiveModules] = useState<ActiveModuleConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initDashboard = async () => {
      setLoading(true);
      try {
        const [systemModules, userConfig] = await Promise.all([
            apiService.getSystemModules(),
            apiService.getUserConfig()
        ]);

        const userModules = userConfig?.modules || [];
        const sysModules = systemModules || [];

        const modules = userModules
          .filter(pref => pref && pref.is_active)
          .map(pref => {
            const details = sysModules.find(sys => sys.id === pref.module_id);
            return details ? { ...details, ...pref } : null;
          })
          .filter(Boolean) as ActiveModuleConfig[];

        // Ordena
        modules.sort((a, b) => a.display_order - b.display_order);
        setActiveModules(modules);

      } catch (error) {
        console.error("Erro ao carregar dashboard:", error);
        setError("Não foi possível carregar seus módulos.");
      } finally {
        setLoading(false);
      }
    };

    initDashboard();
  }, []);

  const handleOnDragEnd = async (result: DropResult) => {
    if (!result.destination) return;
    const items = Array.from(activeModules);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);
    
    const updatedItems = items.map((item, index) => ({ ...item, display_order: index + 1 }));
    setActiveModules(updatedItems);

    // Salva a nova ordem silenciosamente
    const preferences: UserModulePreference[] = updatedItems.map(m => ({
        module_id: m.id, is_active: m.is_active, display_order: m.display_order
    }));
    try { await apiService.updateUserModules(preferences); } catch (e) {}
  };
  
  if (loading) return <div className="flex h-[calc(100vh-80px)] items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div></div>;
  if (error) return <div className="p-8 text-center text-red-500"><p>{error}</p></div>;

  return (
    <main className="p-4 md:p-6 max-w-[1600px] mx-auto">
      <DragDropContext onDragEnd={handleOnDragEnd}>
        <Droppable droppableId="dashboard-modules" direction="horizontal">
          {(provided: DroppableProvided) => (
            <div 
              {...provided.droppableProps} 
              ref={provided.innerRef}
              // GRID RESPONSIVO: 1 col mobile, 2 col tablet, 4 col desktop
              className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 auto-rows-[minmax(300px,auto)]"
            >
              {activeModules.map((module, index) => {
                const AgentComponent = COMPONENT_MAP[module.id];
                if (!AgentComponent) return null;

                return (
                  <Draggable key={module.id} draggableId={module.id} index={index}>
                    {(provided: DraggableProvided, snapshot: DraggableStateSnapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        {...provided.dragHandleProps}
                        style={{ 
                          ...provided.draggableProps.style,
                          // Responsividade no Grid Span
                          gridColumn: window.innerWidth >= 1280 ? `span ${module.grid_column_span}` : 'span 1'
                        }}
                        className={`${snapshot.isDragging ? 'z-50 opacity-90 scale-105' : ''} h-full transition-all duration-200`}
                      >
                        <div className="h-full">
                          <AgentComponent title={module.name} />
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
  );
}

export default DashboardPage;