# UI System Module (Frontend)

## Purpose

This frontend module provides a comprehensive design system and reusable UI components that ensure visual consistency across all other frontend modules. It handles theming, component variants, design tokens, and accessibility without containing any business domain logic.

## Domain Responsibility

**"Providing consistent visual design and reusable UI components to all frontend modules"**

The UI System module owns all visual design concerns:

- Reusable UI components (Button, Card, Progress, etc.)
- Design system and visual consistency
- Theme management (light/dark mode, colors, spacing)
- Typography and iconography systems
- Component variants and styling patterns
- Accessibility features and standards

## Architecture

### Module API (Public Interface)

```typescript
// module_api/index.ts
export { Button, Card, Progress, LoadingSpinner } from './components';
export { useTheme, ThemeProvider } from './theme';
export { lightTheme, darkTheme } from './theme';
export type { Theme, ThemeColors, Spacing, Typography } from './theme';

// module_api/components.ts
export { Button } from '../components/Button';
export { Card } from '../components/Card';
export { Progress } from '../components/Progress';
export { LoadingSpinner } from '../components/LoadingSpinner';
export { ErrorBoundary } from '../components/ErrorBoundary';

// module_api/theme.ts
export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  initialTheme = lightTheme
}) => {
  const [theme, setTheme] = useState(initialTheme);

  const contextValue = {
    theme,
    setTheme,
    toggleTheme: () => setTheme(theme.mode === 'light' ? darkTheme : lightTheme),
    isDark: theme.mode === 'dark',
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};
```

### Components (Reusable UI)

```typescript
// components/Button.tsx
interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  style?: ViewStyle;
  testID?: string;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  icon,
  style,
  testID,
}) => {
  const { theme } = useTheme();

  const buttonStyle = [
    styles.base,
    getVariantStyle(variant, theme),
    getSizeStyle(size, theme),
    disabled && styles.disabled,
    style,
  ];

  return (
    <TouchableOpacity
      style={buttonStyle}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
      testID={testID}
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || loading }}
    >
      {loading ? (
        <ActivityIndicator size="small" color={getLoadingColor(variant, theme)} />
      ) : (
        <View style={styles.content}>
          {icon && <View style={styles.icon}>{icon}</View>}
          <Text style={getTextStyle(variant, size, theme)}>{title}</Text>
        </View>
      )}
    </TouchableOpacity>
  );
};

// components/Card.tsx
interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  padding?: keyof Theme['spacing'] | number;
  shadow?: boolean;
  borderRadius?: number;
  onPress?: () => void;
  testID?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  style,
  padding = 'md',
  shadow = true,
  borderRadius,
  onPress,
  testID,
}) => {
  const { theme } = useTheme();

  const paddingValue = typeof padding === 'number'
    ? padding
    : theme.spacing[padding];

  const cardStyle = [
    styles.base,
    {
      backgroundColor: theme.colors.surface,
      borderColor: theme.colors.border,
      padding: paddingValue,
      borderRadius: borderRadius || theme.borderRadius?.medium || 12,
    },
    shadow && theme.shadows?.medium,
    style,
  ];

  const Component = onPress ? TouchableOpacity : View;

  return (
    <Component
      style={cardStyle}
      onPress={onPress}
      activeOpacity={onPress ? 0.9 : 1}
      testID={testID}
      accessibilityRole={onPress ? "button" : undefined}
    >
      {children}
    </Component>
  );
};

// components/Progress.tsx
interface ProgressProps {
  value: number; // 0-100
  color?: string;
  backgroundColor?: string;
  height?: number;
  animated?: boolean;
  showPercentage?: boolean;
  style?: ViewStyle;
  testID?: string;
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  color,
  backgroundColor,
  height = 8,
  animated = true,
  showPercentage = false,
  style,
  testID,
}) => {
  const { theme } = useTheme();
  const progressValue = useSharedValue(0);

  const defaultColor = color || theme.colors.primary;
  const defaultBackgroundColor = backgroundColor || theme.colors.border;

  useEffect(() => {
    const targetValue = Math.max(0, Math.min(100, value));

    if (animated) {
      progressValue.value = withSpring(targetValue, {
        damping: 15,
        stiffness: 150,
      });
    } else {
      progressValue.value = targetValue;
    }
  }, [value, animated]);

  const animatedStyle = useAnimatedStyle(() => ({
    width: `${progressValue.value}%`,
  }));

  return (
    <View style={[styles.container, style]} testID={testID}>
      <View
        style={[
          styles.track,
          {
            height,
            backgroundColor: defaultBackgroundColor,
            borderRadius: height / 2,
          },
        ]}
      >
        <Animated.View
          style={[
            styles.fill,
            {
              height,
              backgroundColor: defaultColor,
              borderRadius: height / 2,
            },
            animatedStyle,
          ]}
        />
      </View>

      {showPercentage && (
        <Text style={[styles.percentage, { color: theme.colors.text }]}>
          {Math.round(value)}%
        </Text>
      )}
    </View>
  );
};
```

### Theme System (Design Foundation)

```typescript
// theme/theme-manager.ts
export interface ThemeColors {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  success: string;
  warning: string;
  error: string;
  info: string;
}

export interface Spacing {
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
  xxl: number;
}

export interface Typography {
  heading1: TextStyle;
  heading2: TextStyle;
  heading3: TextStyle;
  body: TextStyle;
  caption: TextStyle;
}

export interface Theme {
  mode: 'light' | 'dark';
  colors: ThemeColors;
  spacing: Spacing;
  typography: Typography;
  shadows?: any;
  borderRadius?: {
    small: number;
    medium: number;
    large: number;
  };
}

// Light theme
export const lightTheme: Theme = {
  mode: 'light',
  colors: {
    primary: '#1CB0F6',
    secondary: '#00CD9C',
    accent: '#FF9600',
    background: '#F7F8FA',
    surface: '#FFFFFF',
    text: '#2B2D42',
    textSecondary: '#5E6B73',
    border: '#E5E7EB',
    success: '#22C55E',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  typography: {
    heading1: {
      fontSize: 32,
      fontWeight: Platform.OS === 'ios' ? '700' : 'bold',
      lineHeight: 40,
    },
    heading2: {
      fontSize: 24,
      fontWeight: Platform.OS === 'ios' ? '600' : 'bold',
      lineHeight: 32,
    },
    heading3: {
      fontSize: 20,
      fontWeight: Platform.OS === 'ios' ? '600' : 'bold',
      lineHeight: 28,
    },
    body: {
      fontSize: 16,
      fontWeight: Platform.OS === 'ios' ? '400' : 'normal',
      lineHeight: 24,
    },
    caption: {
      fontSize: 14,
      fontWeight: Platform.OS === 'ios' ? '400' : 'normal',
      lineHeight: 20,
    },
  },
  shadows: {
    small: Platform.select({
      ios: {
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.18,
        shadowRadius: 1.0,
      },
      android: {
        elevation: 2,
      },
    }),
    medium: Platform.select({
      ios: {
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.22,
        shadowRadius: 2.22,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  borderRadius: {
    small: 4,
    medium: 8,
    large: 12,
  },
};

// Dark theme
export const darkTheme: Theme = {
  ...lightTheme,
  mode: 'dark',
  colors: {
    ...lightTheme.colors,
    background: '#1A1A1A',
    surface: '#2D2D2D',
    text: '#FFFFFF',
    textSecondary: '#B0B0B0',
    border: '#404040',
  },
};

export class ThemeManager {
  private currentTheme: Theme;
  private listeners: ThemeChangeListener[];

  constructor(initialTheme: Theme = lightTheme) {
    this.currentTheme = initialTheme;
    this.listeners = [];
  }

  getTheme(): Theme {
    return this.currentTheme;
  }

  setTheme(theme: Theme): void {
    this.currentTheme = theme;
    this.notifyListeners(theme);
    this.persistTheme(theme);
  }

  toggleTheme(): void {
    const newTheme =
      this.currentTheme.mode === 'light' ? darkTheme : lightTheme;
    this.setTheme(newTheme);
  }

  addListener(listener: ThemeChangeListener): void {
    this.listeners.push(listener);
  }

  removeListener(listener: ThemeChangeListener): void {
    const index = this.listeners.indexOf(listener);
    if (index > -1) {
      this.listeners.splice(index, 1);
    }
  }

  private notifyListeners(theme: Theme): void {
    this.listeners.forEach(listener => listener(theme));
  }

  private async persistTheme(theme: Theme): Promise<void> {
    try {
      await AsyncStorage.setItem(
        '@theme_preference',
        JSON.stringify(theme.mode)
      );
    } catch (error) {
      console.warn('Failed to persist theme:', error);
    }
  }
}
```

## Cross-Module Communication

### Provides to Other Modules

- **All Modules**: Consistent UI components, theme system, design tokens
- **Topic Catalog Module**: Button, Card components for topic display
- **Learning Session Module**: Progress component, interactive buttons
- **Learning Analytics Module**: Data visualization components, charts

### Dependencies

- **React Native**: Platform-specific UI components and APIs
- **React Native Reanimated**: For smooth animations
- **AsyncStorage**: For theme persistence

### Communication Examples

```typescript
// All modules use UI System via module_api
import { Button, Card, Progress, useTheme } from '@/modules/ui_system';

// Topic Catalog using UI components
function TopicCard({ topic, onPress }) {
  return (
    <Card onPress={onPress} shadow>
      <Text>{topic.title}</Text>
      <Button title="Start Learning" variant="primary" onPress={onPress} />
    </Card>
  );
}

// Learning Session using progress
function LearningProgress({ progress }) {
  const { theme } = useTheme();

  return (
    <Progress
      value={progress}
      color={theme.colors.success}
      showPercentage
      animated
    />
  );
}
```

## Testing Strategy

### Component Tests

```typescript
// tests/components/Button.test.tsx
describe('Button', () => {
  it('renders with correct title', () => {
    render(
      <ThemeProvider>
        <Button title="Test Button" onPress={jest.fn()} />
      </ThemeProvider>
    );

    expect(screen.getByText('Test Button')).toBeTruthy();
  });

  it('calls onPress when pressed', () => {
    const mockOnPress = jest.fn();

    render(
      <ThemeProvider>
        <Button title="Test" onPress={mockOnPress} />
      </ThemeProvider>
    );

    fireEvent.press(screen.getByText('Test'));
    expect(mockOnPress).toHaveBeenCalled();
  });

  it('shows loading state correctly', () => {
    render(
      <ThemeProvider>
        <Button title="Test" onPress={jest.fn()} loading={true} />
      </ThemeProvider>
    );

    expect(screen.getByTestId('activity-indicator')).toBeTruthy();
    expect(screen.queryByText('Test')).toBeNull();
  });

  it('applies theme colors correctly', () => {
    render(
      <ThemeProvider initialTheme={darkTheme}>
        <Button title="Test" onPress={jest.fn()} variant="primary" />
      </ThemeProvider>
    );

    const button = screen.getByRole('button');
    expect(button.props.style).toContainEqual(
      expect.objectContaining({
        backgroundColor: darkTheme.colors.primary,
      })
    );
  });
});
```

### Theme Tests

```typescript
// tests/theme/theme-manager.test.ts
describe('ThemeManager', () => {
  it('initializes with light theme by default', () => {
    const manager = new ThemeManager();
    expect(manager.getTheme().mode).toBe('light');
  });

  it('toggles between light and dark themes', () => {
    const manager = new ThemeManager();

    manager.toggleTheme();
    expect(manager.getTheme().mode).toBe('dark');

    manager.toggleTheme();
    expect(manager.getTheme().mode).toBe('light');
  });

  it('notifies listeners on theme change', () => {
    const manager = new ThemeManager();
    const listener = jest.fn();

    manager.addListener(listener);
    manager.setTheme(darkTheme);

    expect(listener).toHaveBeenCalledWith(darkTheme);
  });
});
```

## Design System Guidelines

### Component Variants

- **Primary**: Main action buttons (CTA, submit)
- **Secondary**: Supporting actions (cancel, back)
- **Outline**: Subtle actions (filters, options)
- **Ghost**: Minimal actions (links, subtle interactions)

### Spacing Scale

- **xs (4px)**: Tight spacing within components
- **sm (8px)**: Close related elements
- **md (16px)**: Standard component spacing
- **lg (24px)**: Section spacing
- **xl (32px)**: Major layout spacing
- **xxl (48px)**: Page-level spacing

### Accessibility

- **Semantic roles**: All interactive components have proper accessibility roles
- **State communication**: Disabled, loading, and error states are communicated to screen readers
- **Touch targets**: Minimum 44px touch targets for all interactive elements
- **Color contrast**: All text meets WCAG AA contrast requirements

## Performance Considerations

### Component Optimization

- **Memoization**: Components are memoized to prevent unnecessary re-renders
- **Style caching**: Computed styles are cached to avoid recalculation
- **Theme context**: Theme changes trigger minimal re-renders

### Animation Performance

- **Native animations**: Use React Native Reanimated for smooth 60fps animations
- **Layout animations**: Minimize layout thrashing during animations
- **Gesture handling**: Optimize touch interactions for responsiveness

## Anti-Patterns to Avoid

❌ **Business logic in UI components**
❌ **Module-specific styling in shared components**
❌ **Hardcoded values instead of design tokens**
❌ **Platform-specific code in shared components**
❌ **Inconsistent component APIs**

## Module Evolution

This module can be extended with:

- **Advanced Components**: Data tables, charts, complex forms
- **Animation Library**: Shared animation presets and transitions
- **Accessibility Enhancements**: Voice control, high contrast modes
- **Internationalization**: RTL support, localized formatting
- **Design Tools**: Storybook integration, design token exports

The UI System module provides a consistent visual foundation that allows other modules to focus on functionality while maintaining design consistency across the entire application.
