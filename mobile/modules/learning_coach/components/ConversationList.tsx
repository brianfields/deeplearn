import React from 'react';
import { FlatList, View, StyleSheet } from 'react-native';
import type { LearningCoachMessage } from '../models';
import { MessageBubble } from './MessageBubble';

interface Props {
  readonly messages: LearningCoachMessage[];
}

export function ConversationList({ messages }: Props): React.ReactElement {
  return (
    <FlatList
      data={messages}
      renderItem={({ item }) => <MessageBubble message={item} />}
      keyExtractor={(item) => item.id}
      contentContainerStyle={styles.container}
      ListFooterComponent={<View style={styles.footer} />}
    />
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
  },
  footer: {
    height: 32,
  },
});
