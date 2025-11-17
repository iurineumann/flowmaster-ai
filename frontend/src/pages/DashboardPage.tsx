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
import AdoAgentCard from '../agents/AdoAgentCard'; // ✅ Importa o Card do ADO

// Mapa de Componentes
const COMPONENT_MAP: Record<string, React.FC<any>> = {
  'context_agent': ContextCard,
  'skill_agent': SkillCard,
  'reserve_agent': ReserveCard,
  'meeting_agent': ContextCard, // TODO: Criar MeetingCard
  'ado_agent': AdoAgentCard,   // ✅ Mapeado corretamente
};

const DashboardPage: React.FC = () => {
  const [activeModules, setActiveModules] = useState<ActiveModuleConfig[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initDashboard = async () => {
      setLoading(true);
      try {
        const [systemModules, userConfig] = await Promise.all([
            apiService.getSystemModules(),
            apiService.getUserConfig()
        ]);

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
  
  if (loading) {
    return (
        <div className="flex h-[calc(100vh-80px)] items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
    );
  }

  return (
    <main className="p-6 max-w-[1600px] mx-auto">
      <DragDropContext onDragEnd={handleOnDragEnd}>
        <Droppable droppableId="dashboard-modules" direction="horizontal">
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
  );
}

export default DashboardPage;